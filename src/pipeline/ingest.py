import json
import sys


def load_records(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: input file not found: {path}")
        print("Tip: run with --generate to create sample data first.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: could not parse {path} as JSON: {e}")
        sys.exit(1)
