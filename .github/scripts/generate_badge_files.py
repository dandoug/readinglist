import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COVERAGE_FILE = PROJECT_ROOT / "coverage.json"
PYLINT_FILE = PROJECT_ROOT / "pylint.json"

# Badge colors in a 5-step progression
BADGE_COLORS = ["red", "orange", "yellow", "blue", "green"]


def write_json_files(coverage_percentage: str, pylint_score: str):
    # Create JSON objects for badges
    coverage_badge = {
        "schemaVersion": 1,
        "label": "Test Line Coverage",
        "message": f"{coverage_percentage}%",
        "color": _coverage_badge_color(coverage_percentage)
    }
    pylint_badge = {
        "schemaVersion": 1,
        "label": "Pylint Score",
        "message": f"{pylint_score}/10",
        "color": _pylint_badge_color(pylint_score)
    }
    # Save JSON objects to files
    with open(COVERAGE_FILE, "w") as coverage_file:
        json.dump(coverage_badge, coverage_file)
    with open(PYLINT_FILE, "w") as pylint_file:
        json.dump(pylint_badge, pylint_file)


def _pylint_badge_color(pylint_score):
    if float(pylint_score) < 3:
        return BADGE_COLORS[0]
    elif float(pylint_score) < 5:
        return BADGE_COLORS[1]
    elif float(pylint_score) < 6:
        return BADGE_COLORS[2]
    elif float(pylint_score) < 7:
        return BADGE_COLORS[3]
    else:
        return BADGE_COLORS[4]


def _coverage_badge_color(coverage_percentage):
    if float(coverage_percentage) < 50:
        return BADGE_COLORS[0]
    elif float(coverage_percentage) < 70:
        return BADGE_COLORS[1]
    elif float(coverage_percentage) < 80:
        return BADGE_COLORS[2]
    elif float(coverage_percentage) < 90:
        return BADGE_COLORS[3]
    else:
        return BADGE_COLORS[4]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate badge JSON files for coverage and pylint scores.")
    parser.add_argument("coverage_percentage", type=float, help="Coverage percentage (e.g., 81.25)")
    parser.add_argument("pylint_score", type=float, help="Pylint score (e.g., 9.5)")
    args = parser.parse_args()

    write_json_files(str(args.coverage_percentage), str(args.pylint_score))
