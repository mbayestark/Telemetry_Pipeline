import json
import random
import os
from datetime import datetime, timedelta

DEVICES = ["DEV_001", "DEV_002", "DEV_003", "DEV_004", "DEV_005"]

VALID_RANGES = {
    "temperature": (18, 70),
    "battery": (0, 100),
    "signal_strength": (-120, 0)
}


def generate_timestamp(base, offset_minutes):
    return (base + timedelta(minutes=offset_minutes)).isoformat()


def generate_clean_record(device_id, timestamp):
    return {
        "device_id": device_id,
        "timestamp": timestamp,
        "temperature": round(random.uniform(18, 70), 2),
        "battery": round(random.uniform(0, 100), 2),
        "signal_strength": round(random.uniform(-120, 0), 2)
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
        record = {
            "device_id": random.choice(DEVICES),
            "timestamp": generate_timestamp(base, 210 + offset * 5),
            "temperature": round(random.uniform(18, 70), 2),
            "battery": round(random.uniform(0, 100), 2),
            "signal_strength": round(random.uniform(-120, 0), 2)
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
            **values
        })

    # 3. Duplicate records (4 records) — only duplicate clean dict records
    for i in random.sample(range(50), 4):
        records.append(records[i].copy())

    # 4. Out-of-order timestamps (4 records)
    for j in range(4):
        records.append({
            "device_id": random.choice(DEVICES),
            "timestamp": generate_timestamp(base, -500 + j * 10),
            "temperature": round(random.uniform(18, 70), 2),
            "battery": round(random.uniform(0, 100), 2),
            "signal_strength": round(random.uniform(-120, 0), 2)
        })

    # 5. Malformed / garbage lines (4 records)
    records.append("GARBAGE_LINE_$$##@@")
    records.append("null")
    records.append({
        "device_id": None,
        "timestamp": "not-a-timestamp",
        "temperature": "hot",
        "battery": "full",
        "signal_strength": "strong"
    })
    records.append({
        "device_id": "DEV_003",
        "timestamp": "not-a-timestamp",
        "temperature": "N/A",
        "battery": None,
        "signal_strength": -60.0
    })

    return records


def generate_dataset(path="data/telemetry.json", n_clean=200):
    base = datetime(2026, 6, 1, 0, 0, 0)
    records = []

    for i in range(n_clean):
        device = random.choice(DEVICES)
        timestamp = generate_timestamp(base, i * 5)
        records.append(generate_clean_record(device, timestamp))

    records = inject_messy_records(records)

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Generated {len(records)} records -> {path}")


if __name__ == "__main__":
    generate_dataset()