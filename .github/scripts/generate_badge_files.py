import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COVERAGE_FILE = PROJECT_ROOT / "coverage.json"
PYLINT_FILE = PROJECT_ROOT / "pylint.json"


def write_json_files(coverage_percentage:str, pylint_score:str):
    # Create JSON objects for badges
    coverage_badge = {
        "schemaVersion": 1,
        "label": "Test Line Coverage",
        "message": f"{coverage_percentage}%",
        "color": "green" if float(coverage_percentage) >= 80 else "red"
    }
    pylint_badge = {
        "schemaVersion": 1,
        "label": "Pylint Score",
        "message": f"{pylint_score}/10",
        "color": "green" if float(pylint_score) >= 7 else "red"
    }
    # Save JSON objects to files
    with open(COVERAGE_FILE, "w") as coverage_file:
        json.dump(coverage_badge, coverage_file)
    with open(PYLINT_FILE, "w") as pylint_file:
        json.dump(pylint_badge, pylint_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate badge JSON files for coverage and pylint scores.")
    parser.add_argument("coverage_percentage", type=float, help="Coverage percentage (e.g., 81.25)")
    parser.add_argument("pylint_score", type=float, help="Pylint score (e.g., 9.5)")
    args = parser.parse_args()

    write_json_files(str(args.coverage_percentage), str(args.pylint_score))
