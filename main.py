"""
Telemetry data-pipeline — main entry point.

Pipeline:
    ingest -> validate & clean -> group & sort -> aggregate -> alert -> output

Usage:
    python main.py                          # use defaults
    python main.py --generate               # regenerate sample data first
    python main.py --input data/telemetry.json --output output/results.json
"""
import argparse

from src.generator import generate_dataset
from src.pipeline.ingest import load_records
from src.pipeline.validator import process_records
from src.utils import group_and_sort
from src.pipeline.aggregator import aggregate_records
from src.pipeline.alert import check_alerts
from src.output import write_output, print_run_summary


def run_pipeline(input_path, output_path):
    raw = load_records(input_path)
    stats = process_records(raw)
    grouped = group_and_sort(stats["clean"])
    summary = aggregate_records(grouped)
    alerts = check_alerts(grouped)

    out_path = write_output(summary, alerts, output_path)
    print_run_summary(stats, summary, alerts)
    print(f"\nStructured results written to: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Telemetry data-pipeline")
    parser.add_argument("--input", default="data/telemetry.json",
                        help="path to input telemetry JSON")
    parser.add_argument("--output", default="output/results.json",
                        help="path to write structured results")
    parser.add_argument("--generate", action="store_true",
                        help="regenerate sample data before running")
    args = parser.parse_args()

    if args.generate:
        generate_dataset(args.input)

    run_pipeline(args.input, args.output)


if __name__ == "__main__":
    main()
