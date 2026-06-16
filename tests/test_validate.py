from src.pipeline.validator import validate_record, deduplicate, process_records


def _good_record(**overrides):
    record = {
        "device_id": "DEV_001",
        "timestamp": "2026-06-01T00:00:00",
        "temperature": 25.0,
        "battery": 80.0,
        "signal_strength": -60.0,
    }
    record.update(overrides)
    return record


def test_valid_record():
    ok, reason = validate_record(_good_record())
    assert ok is True
    assert reason is None


def test_malformed_non_dict():
    ok, reason = validate_record("GARBAGE")
    assert ok is False
    assert reason == "malformed"


def test_missing_field():
    record = _good_record()
    del record["battery"]
    ok, reason = validate_record(record)
    assert ok is False
    assert reason == "missing_field"


def test_invalid_device_id_null():
    ok, reason = validate_record(_good_record(device_id=None))
    assert ok is False
    assert reason == "invalid_device_id"


def test_invalid_device_id_empty():
    ok, reason = validate_record(_good_record(device_id=""))
    assert ok is False
    assert reason == "invalid_device_id"


def test_invalid_timestamp():
    ok, reason = validate_record(_good_record(timestamp="not-a-timestamp"))
    assert ok is False
    assert reason == "invalid_timestamp"


def test_invalid_type_string():
    ok, reason = validate_record(_good_record(temperature="hot"))
    assert ok is False
    assert reason == "invalid_type"


def test_invalid_type_bool():
    ok, reason = validate_record(_good_record(battery=True))
    assert ok is False
    assert reason == "invalid_type"


def test_out_of_range_temperature_high():
    ok, reason = validate_record(_good_record(temperature=150.0))
    assert ok is False
    assert reason == "out_of_range"


def test_out_of_range_battery_negative():
    ok, reason = validate_record(_good_record(battery=-10.0))
    assert ok is False
    assert reason == "out_of_range"


def test_boundary_values_accepted():
    ok, _ = validate_record(_good_record(temperature=-40, battery=0, signal_strength=-120))
    assert ok is True
    ok, _ = validate_record(_good_record(temperature=85, battery=100, signal_strength=0))
    assert ok is True


def test_removes_exact_duplicates():
    record = _good_record()
    unique, count = deduplicate([record, record.copy(), record.copy()])
    assert len(unique) == 1
    assert count == 2


def test_keeps_distinct_records():
    r1 = _good_record()
    r2 = _good_record(device_id="DEV_002", timestamp="2026-06-01T00:05:00",
                       temperature=30.0, battery=70.0, signal_strength=-55.0)
    unique, count = deduplicate([r1, r2])
    assert len(unique) == 2
    assert count == 0


def test_process_records_counts_add_up():
    records = [_good_record(), "GARBAGE", {"temperature": 25.0}]
    stats = process_records(records)
    assert len(stats["clean"]) + stats["rejected_total"] == stats["total_read"]
