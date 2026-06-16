from datetime import datetime

from src.config import (
    BATTERY_THRESHOLD,
    TEMP_HIGH_THRESHOLD,
    TEMP_LOW_THRESHOLD,
    MAX_GAP_MINUTES,
)


def check_alerts(grouped):
    alerts = []

    for device_id, records in grouped.items():
        latest_battery = records[-1]["battery"]
        if latest_battery < BATTERY_THRESHOLD:
            alerts.append({
                "device_id": device_id,
                "alert_type": "low_battery",
                "details": {"latest_battery": latest_battery}
            })

        temps = [r["temperature"] for r in records]
        if max(temps) > TEMP_HIGH_THRESHOLD or min(temps) < TEMP_LOW_THRESHOLD:
            alerts.append({
                "device_id": device_id,
                "alert_type": "temperature_out_of_range",
                "details": {
                    "min_temp": round(min(temps), 2),
                    "max_temp": round(max(temps), 2),
                }
            })

        max_gap = 0.0
        for i in range(1, len(records)):
            prev = datetime.fromisoformat(records[i - 1]["timestamp"])
            curr = datetime.fromisoformat(records[i]["timestamp"])
            gap = (curr - prev).total_seconds() / 60
            if gap > max_gap:
                max_gap = gap

        if max_gap > MAX_GAP_MINUTES:
            alerts.append({
                "device_id": device_id,
                "alert_type": "reporting_gap",
                "details": {"max_gap_minutes": round(max_gap, 1)}
            })

    return alerts
