from datetime import datetime
from generator import VALID_RANGES

REQUIRED_FIELDS = ["device_id", "timestamp", "temperature", "battery", "signal_strength"]
NUMERIC_FIELDS = ["temperature", "battery", "signal_strength"]


def validate_record(record):
    """
    Validate a single record.
    Returns (True, None) if valid, otherwise (False, reason).
    """
    # 1. Must be a dictionary (rejects raw garbage strings)
    if not isinstance(record, dict):
        return False, "malformed"

    # 2. All required fields present
    for field in REQUIRED_FIELDS:
        if field not in record:
            return False, "missing_field"

    # 3. device_id must be a non-empty string
    if not isinstance(record["device_id"], str) or not record["device_id"]:
        return False, "invalid_device_id"

    # 4. timestamp must be a parseable ISO string
    if not isinstance(record["timestamp"], str):
        return False, "invalid_timestamp"
    try:
        datetime.fromisoformat(record["timestamp"])
    except ValueError:
        return False, "invalid_timestamp"

    # 5. numeric fields must be real numbers (bool excluded:
    #    isinstance(True, int) is True in Python)
    for field in NUMERIC_FIELDS:
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, "invalid_type"

    # 6. numeric fields must be within valid range
    for field in NUMERIC_FIELDS:
        low, high = VALID_RANGES[field]
        if not (low <= record[field] <= high):
            return False, "out_of_range"

    return True, None


def deduplicate(records):
    """
    Remove exact duplicate records (same device_id, timestamp, and readings).
    Returns (unique_records, duplicate_count).
    Assumes all input records are already validated dicts.
    """
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
    """
    Run the full validation + dedup stage over a batch of raw records.

    Returns a dict:
      {
        "clean": [...],                # valid, de-duplicated records
        "rejected_total": int,
        "rejected_by_reason": {reason: count, ...},
        "duplicates": int,
        "total_read": int,
      }
    """
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