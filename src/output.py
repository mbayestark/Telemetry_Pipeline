import json
import os


def write_output(summary, alerts, grouped, path="output/results.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    clean_series = {}
    for device_id, records in grouped.items():
        clean_series[device_id] = [
            {
                "timestamp": r["timestamp"],
                "temperature": r["temperature"],
                "battery": r["battery"],
                "signal_strength": r["signal_strength"],
            }
            for r in records
        ]

    payload = {
        "device_summary": summary,
        "alerts": alerts,
        "clean_series": clean_series,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def print_run_summary(stats, summary, alerts):
    """
    Print a short, human-readable run summary to the console.

    stats: the dict returned by validator.process_records
    """
    print("=" * 50)
    print("RUN SUMMARY")
    print("=" * 50)
    print(f"Records read     : {stats['total_read']}")
    print(f"Records accepted : {len(stats['clean'])}")
    print(f"Records rejected : {stats['rejected_total']}")

    if stats["rejected_by_reason"]:
        print("  Rejected by reason:")
        for reason, count in sorted(stats["rejected_by_reason"].items()):
            print(f"    - {reason}: {count}")

    print(f"Devices summarized: {len(summary)}")
    print(f"Alerts generated  : {len(alerts)}")

    if alerts:
        print("  Alerts:")
        for a in alerts:
            print(f"    - {a['device_id']}: {a['alert_type']} {a['details']}")
    print("=" * 50)