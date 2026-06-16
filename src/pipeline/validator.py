from datetime import datetime

from src.config import VALID_RANGES

REQUIRED_FIELDS = ["device_id", "timestamp", "temperature", "battery", "signal_strength"]
NUMERIC_FIELDS = ["temperature", "battery", "signal_strength"]


def validate_record(record):
    if not isinstance(record, dict):
        return False, "malformed"

    for field in REQUIRED_FIELDS:
        if field not in record:
            return False, "missing_field"

    if not isinstance(record["device_id"], str) or not record["device_id"]:
        return False, "invalid_device_id"

    if not isinstance(record["timestamp"], str):
        return False, "invalid_timestamp"
    try:
        datetime.fromisoformat(record["timestamp"])
    except ValueError:
        return False, "invalid_timestamp"

    for field in NUMERIC_FIELDS:
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, "invalid_type"

    for field in NUMERIC_FIELDS:
        low, high = VALID_RANGES[field]
        if not (low <= record[field] <= high):
            return False, "out_of_range"

    return True, None


def deduplicate(records):
    seen = set()
    unique = []
    duplicates = 0

    for record in records:
        signature = (
            record["device_id"],
            record["timestamp"],
            record["temperature"],
            record["battery"],
            record["signal_strength"],
        )
        if signature in seen:
            duplicates += 1
        else:
            seen.add(signature)
            unique.append(record)

    return unique, duplicates


def process_records(raw_records):
    valid = []
    rejected_by_reason = {}

    for record in raw_records:
        ok, reason = validate_record(record)
        if ok:
            valid.append(record)
        else:
            rejected_by_reason[reason] = rejected_by_reason.get(reason, 0) + 1

    clean, duplicates = deduplicate(valid)
    if duplicates:
        rejected_by_reason["duplicate"] = duplicates

    return {
        "clean": clean,
        "rejected_total": sum(rejected_by_reason.values()),
        "rejected_by_reason": rejected_by_reason,
        "duplicates": duplicates,
        "total_read": len(raw_records),
    }
