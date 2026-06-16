import json
import random
import os
from datetime import datetime, timedelta

from src.config import (
    DEVICES,
    VALID_RANGES,
    NORMAL_TEMP_RANGE,
    DEFAULT_CLEAN_RECORDS,
    NORMAL_INTERVAL_MINUTES,
)


def generate_timestamp(base, offset_minutes):
    return (base + timedelta(minutes=offset_minutes)).isoformat()


def generate_clean_record(device_id, timestamp):
    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "temperature": round(random.uniform(*NORMAL_TEMP_RANGE), 2),
        "battery": round(random.uniform(*VALID_RANGES["battery"]), 2),
        "signal_strength": round(random.uniform(*VALID_RANGES["signal_strength"]), 2),
    }


def inject_messy_records(records):
    base = datetime(2026, 6, 1, 0, 0, 0)

    # 1. Missing fields (6 records)
    missing_configs = [
        ["temperature"],
        ["battery"],
        ["signal_strength"],
        ["temperature", "battery"],
        ["signal_strength", "battery"],
        ["device_id"],
    ]
    for offset, missing in enumerate(missing_configs):
        record = generate_clean_record(random.choice(DEVICES),
                                       generate_timestamp(base, 210 + offset * 5))
        for field in missing:
            del record[field]
        records.append(record)

    # 2. Out-of-range values (6 records)
    out_of_range = [
        {"temperature": 150.0, "battery": 50.0, "signal_strength": -60.0},
        {"temperature": -100.0, "battery": 50.0, "signal_strength": -60.0},
        {"temperature": 40.0, "battery": -10.0, "signal_strength": -60.0},
        {"temperature": 40.0, "battery": 150.0, "signal_strength": -60.0},
        {"temperature": 40.0, "battery": 50.0, "signal_strength": 50.0},
        {"temperature": 40.0, "battery": 50.0, "signal_strength": -200.0},
    ]
    for offset, values in enumerate(out_of_range):
        records.append({
            "device_id": random.choice(DEVICES),
            "timestamp": generate_timestamp(base, 260 + offset * 5),
            **values,
        })

    # 3. Duplicate records (4) — only duplicate clean dict records
    for i in random.sample(range(50), 4):
        records.append(records[i].copy())

    # 4. Out-of-order timestamps (4)
    for j in range(4):
        records.append(generate_clean_record(
            random.choice(DEVICES),
            generate_timestamp(base, -500 + j * 10)
        ))

    # 5. Malformed / garbage lines (4)
    records.append("GARBAGE_LINE_$$##@@")
    records.append("null")
    records.append({
        "device_id": None,
        "timestamp": "not-a-timestamp",
        "temperature": "hot",
        "battery": "full",
        "signal_strength": "strong",
    })
    records.append({
        "device_id": "DEV_003",
        "timestamp": "not-a-timestamp",
        "temperature": "N/A",
        "battery": None,
        "signal_strength": -60.0,
    })

    # 6. Anomalous-but-VALID readings — these pass validation but should trip
    #    alerts: a dangerously hot reading and a critically low LATEST battery.
    #    This proves alerting fires on real, in-range data, not just on garbage.
    #    Late timestamps (offset 2000+) ensure the battery record is the most
    #    recent for its device, so the "latest battery" check sees it.
    records.append({
        "device_id": "DEV_001",
        "timestamp": generate_timestamp(base, 2000),
        "temperature": 78.0,   # above TEMP_HIGH_THRESHOLD, within VALID_RANGES
        "battery": 60.0,
        "signal_strength": -50.0,
    })
    records.append({
        "device_id": "DEV_002",
        "timestamp": generate_timestamp(base, 2005),
        "temperature": 40.0,
        "battery": 5.0,        # below BATTERY_THRESHOLD — critical latest battery
        "signal_strength": -55.0,
    })

    return records


def generate_dataset(path="data/telemetry.json", n_clean=DEFAULT_CLEAN_RECORDS):
    base = datetime(2026, 6, 1, 0, 0, 0)
    records = []

    for i in range(n_clean):
        device = random.choice(DEVICES)
        timestamp = generate_timestamp(base, i * NORMAL_INTERVAL_MINUTES)
        records.append(generate_clean_record(device, timestamp))

    records = inject_messy_records(records)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Generated {len(records)} records -> {path}")


if __name__ == "__main__":
    generate_dataset()