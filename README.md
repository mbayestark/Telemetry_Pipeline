# Telemetry Data-Pipeline

A small, robust pipeline that ingests a stream of device telemetry readings,
validates and cleans messy real-world data, computes per-device aggregates,
and raises alerts when something looks wrong.

Built for the Praxtion Telemetry Data-Pipeline mini-assessment.

---

## What it does

Given a stream of sensor readings — each with a device ID, timestamp,
temperature, battery level, and signal strength — the pipeline:

1. **Ingests** records from a JSON file.
2. **Validates and cleans** each record: rejects malformed lines, missing
   fields, wrong types, out-of-range values, and bad timestamps; de-duplicates
   exact repeats. Bad records are counted by reason, never crashed on.
3. **Aggregates** per device: reading count, min/max/average temperature,
   latest battery level, and the time span covered.
4. **Alerts** on conditions that matter: critically low battery, temperature
   outside a safe band, and reporting gaps (a device that went quiet).
5. **Writes** a single structured JSON output file and prints a run summary.

---

## Project structure

```
.
├── main.py                  # Entry point — ties the pipeline together
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py            # All tunable parameters (ranges, thresholds, devices)
│   ├── generator.py         # Generates the messy sample dataset
│   ├── utils.py             # Shared helper: group_and_sort
│   ├── output.py            # Structured output file + console run summary
│   └── pipeline/
│       ├── __init__.py
│       ├── ingest.py        # Load raw records from file
│       ├── validator.py     # Validation, rejection-by-reason, de-duplication
│       ├── aggregator.py    # Per-device aggregate statistics
│       └── alert.py         # Alert detection (battery / temperature / gaps)
├── tests/
│   └── test_validate.py     # Unit tests (including deliberately malformed records)
├── data/                    # Generated input data (created on run)
└── output/                  # Pipeline results (created on run)
```

The data flows in one direction through clearly separated stages:

```
ingest → validate & clean → group & sort → aggregate → alert → output
```

---

## How to run

Requires **Python 3.9+**.

```bash
pip install -r requirements.txt
```

```bash
# 1. Generate sample data and run the full pipeline in one step
python main.py --generate

# 2. Or, if data already exists, just run the pipeline
python main.py

# 3. Point it at a custom input / output path
python main.py --input data/telemetry.json --output output/results.json
```

To regenerate the sample dataset on its own:

```bash
python -m src.generator
```

To run the tests:

```bash
python -m pytest tests/
```

---

## Sample data — what messy conditions are injected

The generator produces ~200 clean records across 5 devices reporting every
5 minutes, then deliberately injects ~26 problem records so the pipeline's
handling is visible. Each injected category and how the pipeline handles it:

| Injected condition        | Example                                      | How the pipeline handles it                          |
|---------------------------|----------------------------------------------|------------------------------------------------------|
| Missing fields            | record with no `battery` key                 | Rejected, counted as `missing_field`                 |
| Out-of-range values       | `temperature: 150`, `battery: -10`           | Rejected, counted as `out_of_range`                  |
| Wrong types               | `temperature: "hot"`, `battery: "full"`      | Rejected, counted as `invalid_type`                  |
| Null / bad device ID      | `device_id: null`                            | Rejected, counted as `invalid_device_id`             |
| Bad timestamp             | `timestamp: "not-a-timestamp"`               | Rejected, counted as `invalid_timestamp`             |
| Garbage / malformed lines | a raw string in the JSON array               | Rejected, counted as `malformed`                     |
| Duplicate records         | an exact copy of an existing reading         | Removed, counted as `duplicate`                      |
| Out-of-order timestamps   | a reading time-stamped before the run start  | Accepted; records are sorted by time before use      |
| Anomalous-but-valid       | `temperature: 78`, `battery: 5`              | Accepted — these are valid readings that trip alerts |

The last category is deliberate: a dangerously hot reading or a near-empty
battery is **not** a data error — it is exactly the kind of valid reading the
**alerting** layer should catch. Injecting these proves the alerts fire on
real, in-range data, not only on garbage.

---

## Pipeline design

The pipeline is split into single-responsibility modules so each stage can be
read, tested, and changed in isolation.

- **`generator.py`** produces the sample stream. Kept separate so the pipeline
  itself never depends on how data was created.
- **`validator.py`** is the heart of the robustness story. `validate_record`
  returns `(True, None)` or `(False, reason)` so every rejection carries a
  reason that can be counted. Checks run cheapest-first and in a safe order:
  is-it-a-dict → required fields → types → ranges → timestamp parse. The
  dict check comes first so a raw garbage string can never crash a later
  field access. De-duplication runs after validation, using a set of record
  signatures for O(n) detection.
- **`utils.group_and_sort`** groups clean records by device and sorts each
  device's readings by timestamp **once**. Both the aggregator and the alerter
  consume this shared, already-sorted structure, so neither repeats the work
  and "latest" and "gap" calculations are always correct.
- **`aggregator.py`** and **`alert.py`** are siblings that each take the
  grouped data and produce their own result, with no dependency on each other.
- **`output.py`** is the only module that writes to disk / prints, keeping I/O
  out of the processing logic.
- **`config.py`** centralizes every tunable value — valid ranges, alert
  thresholds, device list, reporting interval — so the system can be tuned in
  one place without touching logic.

A subtle but important design point: the **valid sensor range** (used by the
validator) is intentionally wider than the **normal operating band** (used to
generate clean data). This lets a genuinely hot reading remain a *valid*
reading that the alerter flags, instead of being thrown away by the validator.
Tying those two together would make it impossible for a temperature alert to
ever fire on valid data.

---

## Example run

```
Records read     : 226
Records accepted : 206
Records rejected : 20
  Rejected by reason:
    - duplicate: 4
    - invalid_device_id: 1
    - invalid_timestamp: 1
    - malformed: 2
    - missing_field: 6
    - out_of_range: 6
Devices summarized: 5
Alerts generated  : 8
  Alerts:
    - DEV_002: low_battery {'latest_battery': 5.0}
    - DEV_001: temperature_out_of_range {'min_temp': 20.02, 'max_temp': 78.0}
    - DEV_005: low_battery {'latest_battery': 19.89}
    - ... (reporting_gap alerts per device)
```

The full per-device summary and the complete alert list are written to
`output/results.json`.

---

## Trade-offs given the time limit

- **Batch, not streaming.** The pipeline reads the whole file at once. This is
  simpler and correct for the dataset size. The stage separation means a real
  streaming ingest could be swapped in without touching validation or
  aggregation.
- **In-memory only.** No database. Results are written to a JSON file. Fine for
  a few hundred records; a real fleet would need persistence.
- **Exact-match de-duplication.** Two readings are duplicates only if every
  field matches. A real system might treat "same device + same timestamp" as a
  duplicate even if a value differs slightly.
- **Gap detection is per-pair.** It flags the largest gap between consecutive
  readings. It does not yet distinguish a device that stopped *now* from one
  that had a gap earlier and recovered.

## What I would build next

- **True streaming** ingest (line-by-line or a queue) with incremental
  aggregates, instead of a single batch pass.
- **Persistence** to a small database (SQLite) so history survives across runs.
- **A dashboard** charting each device's readings over time with alerts marked.
- **Scaling** to many devices: partition by device, process in parallel.
- **Richer alerts**: severity levels, "device offline" vs "temporary gap",
  and de-duplicating repeated alerts for the same ongoing condition.

---

## AI tools used

An AI coding assistant (Claude) was used as a pair-programming aid to discuss
design, review my code, and catch edge cases. All design decisions, the
validation logic, and the final structure were worked through and understood by
me; I can explain any part of the submission.

## Effort

Roughly **[FILL IN] hours** end to end, including design, implementation,
testing, and documentation.
