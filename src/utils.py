from datetime import datetime


def group_and_sort(records):
    """
    Group records by device_id and sort each device's list by timestamp.

    Input:  flat list of clean record dicts
    Output: { device_id: [record, record, ...sorted by time...], ... }
    """
    grouped = {}
    for record in records:
        grouped.setdefault(record["device_id"], []).append(record)

    for device_id in grouped:
        grouped[device_id].sort(
            key=lambda r: datetime.fromisoformat(r["timestamp"])
        )

    return grouped