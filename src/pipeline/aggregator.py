from datetime import datetime


def aggregate_records(grouped):
    summary = {}
    for device_id, device_records in grouped.items():
        temps = [r["temperature"] for r in device_records]
        first_ts = datetime.fromisoformat(device_records[0]["timestamp"])
        last_ts = datetime.fromisoformat(device_records[-1]["timestamp"])

        summary[device_id] = {
            "reading_count": len(device_records),
            "min_temperature": round(min(temps), 2),
            "max_temperature": round(max(temps), 2),
            "avg_temperature": round(sum(temps) / len(temps), 2),
            "latest_battery": device_records[-1]["battery"],
            "first_reading": first_ts.isoformat(),
            "last_reading": last_ts.isoformat(),
            "time_span_minutes": round((last_ts - first_ts).total_seconds() / 60, 1),
        }

    return summary
