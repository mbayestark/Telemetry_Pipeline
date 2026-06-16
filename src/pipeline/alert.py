from datetime import datetime

from src.config import (
    BATTERY_THRESHOLD,
    TEMP_HIGH_THRESHOLD,
    TEMP_LOW_THRESHOLD,
    MAX_GAP_MINUTES,
    MAX_TEMP_CHANGE_PER_MINUTE,
    MAX_BATTERY_CHANGE_PER_MINUTE,
)


def check_alerts(grouped):
    alerts = []

    latest_global = max(
        datetime.fromisoformat(records[-1]["timestamp"])
        for records in grouped.values()
    )

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
            prev_ts = datetime.fromisoformat(records[i - 1]["timestamp"])
            curr_ts = datetime.fromisoformat(records[i]["timestamp"])
            minutes = (curr_ts - prev_ts).total_seconds() / 60

            if minutes > max_gap:
                max_gap = minutes

            if minutes > 0:
                temp_rate = abs(records[i]["temperature"] - records[i - 1]["temperature"]) / minutes
                batt_rate = abs(records[i]["battery"] - records[i - 1]["battery"]) / minutes

                if temp_rate > MAX_TEMP_CHANGE_PER_MINUTE:
                    alerts.append({
                        "device_id": device_id,
                        "alert_type": "anomalous_temp_change",
                        "details": {
                            "from": records[i - 1]["temperature"],
                            "to": records[i]["temperature"],
                            "rate_per_min": round(temp_rate, 2),
                            "interval_minutes": round(minutes, 1),
                        }
                    })

                if batt_rate > MAX_BATTERY_CHANGE_PER_MINUTE:
                    alerts.append({
                        "device_id": device_id,
                        "alert_type": "anomalous_battery_change",
                        "details": {
                            "from": records[i - 1]["battery"],
                            "to": records[i]["battery"],
                            "rate_per_min": round(batt_rate, 2),
                            "interval_minutes": round(minutes, 1),
                        }
                    })

        last_ts = datetime.fromisoformat(records[-1]["timestamp"])
        silence = (latest_global - last_ts).total_seconds() / 60

        if silence > MAX_GAP_MINUTES:
            alerts.append({
                "device_id": device_id,
                "alert_type": "device_offline",
                "details": {
                    "last_seen": last_ts.isoformat(),
                    "silent_minutes": round(silence, 1),
                }
            })

        if max_gap > MAX_GAP_MINUTES:
            alerts.append({
                "device_id": device_id,
                "alert_type": "reporting_gap_recovered",
                "details": {"max_gap_minutes": round(max_gap, 1)}
            })

    return alerts
