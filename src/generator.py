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


def clamp(value, low, high):
    return max(low, min(high, value))


def drift(value, max_step, low, high):
    return round(clamp(value + random.uniform(-max_step, max_step), low, high), 2)


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
        record = {
            "device_id": random.choice(DEVICES),
            "timestamp": generate_timestamp(base, 210 + offset * 5),
            "temperature": 35.0,
            "battery": 70.0,
            "signal_strength": -60.0,
        }
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
        records.append({
            "device_id": random.choice(DEVICES),
            "timestamp": generate_timestamp(base, -500 + j * 10),
            "temperature": 35.0,
            "battery": 70.0,
            "signal_strength": -60.0,
        })

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

    # 7. Rate-of-change anomalies — both values are individually valid, but
    #    the jump between consecutive readings is physically implausible.
    #    Timestamps are 5 min apart so the rate check fires.
    records.append({
        "device_id": "DEV_003",
        "timestamp": generate_timestamp(base, 100),
        "temperature": 25.0,
        "battery": 90.0,
        "signal_strength": -50.0,
    })
    records.append({
        "device_id": "DEV_003",
        "timestamp": generate_timestamp(base, 105),
        "temperature": 55.0,       # +30°C in 5 min = 6°C/min (threshold: 2)
        "battery": 90.0,
        "signal_strength": -50.0,
    })
    records.append({
        "device_id": "DEV_004",
        "timestamp": generate_timestamp(base, 100),
        "temperature": 30.0,
        "battery": 85.0,
        "signal_strength": -55.0,
    })
    records.append({
        "device_id": "DEV_004",
        "timestamp": generate_timestamp(base, 105),
        "temperature": 30.0,
        "battery": 50.0,           # -35% in 5 min = 7%/min (threshold: 1)
        "signal_strength": -55.0,
    })

    return records


def generate_dataset(path="data/telemetry.json", n_clean=DEFAULT_CLEAN_RECORDS, seed=42):
    random.seed(seed)
    base = datetime(2026, 6, 1, 0, 0, 0)
    records = []
    readings_per_device = n_clean // len(DEVICES)

    for device_id in DEVICES:
        temp = random.uniform(*NORMAL_TEMP_RANGE)
        battery = random.uniform(60, 95)
        signal = random.uniform(-80, -40)

        for i in range(readings_per_device):
            timestamp = generate_timestamp(base, i * NORMAL_INTERVAL_MINUTES)
            temp = drift(temp, 1.5, *NORMAL_TEMP_RANGE)
            battery = drift(battery, 0.8, *VALID_RANGES["battery"])
            signal = drift(signal, 3.0, *VALID_RANGES["signal_strength"])

            records.append({
                "device_id": device_id,
                "timestamp": timestamp,
                "temperature": temp,
                "battery": battery,
                "signal_strength": signal,
            })

    records = inject_messy_records(records)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Generated {len(records)} records -> {path}")


if __name__ == "__main__":
    generate_dataset()