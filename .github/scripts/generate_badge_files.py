import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COVERAGE_FILE = PROJECT_ROOT / "coverage.json"
PYLINT_FILE = PROJECT_ROOT / "pylint.json"
BANDIT_FILE = PROJECT_ROOT / "bandit.json"
RANDON_CC_FILE = PROJECT_ROOT / "radon_cc.json"
RADON_LOC_FILE = PROJECT_ROOT / "radon_loc.json"
PROSPECTOR_MSG_COUNT_FILE = PROJECT_ROOT / "prospector_msg_count.json"

# Badge colors in a 5-step progression
BADGE_COLORS = ["red", "orange", "yellow", "blue", "green"]


def write_json_files(coverage_percentage: str, pylint_score: str, bandit_sev_hits: str,
                     radon_cc: str, radon_loc: str, prospector_msgs: str,):
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
    bandit_badge = {
        "schemaVersion": 1,
        "label": "Bandit Severe Hits",
        "message": f"{bandit_sev_hits}",
        "color": _bandit_badge_color(int(bandit_sev_hits))
    }
    radon_cc_badge = {
        "schemaVersion": 1,
        "label": "Cyclomatic Complexity",
        "message": f"{float(radon_cc):.2f}",
        "color": _radon_cc_color(float(radon_cc))
    }
    radon_loc_badge = {
        "schemaVersion": 1,
        "label": "Lines of Code",
        "message": f"{radon_loc}",
        "color": "lightgrey"
    }
    msg_count_ratio = float(prospector_msgs) / float(radon_loc)
    prospector_msgs_badge = {
        "schemaVersion": 1,
        "label": "Prospector Messages Rate",
        "message": f"{msg_count_ratio*100:.2f}% ({prospector_msgs}/{radon_loc})",
        "color": _prospector_msg_ratio_color(msg_count_ratio)
    }
    # Save JSON objects to files
    with open(COVERAGE_FILE, "w", encoding='utf-8') as coverage_file:
        json.dump(coverage_badge, coverage_file)
    with open(PYLINT_FILE, "w", encoding='utf-8') as pylint_file:
        json.dump(pylint_badge, pylint_file)
    with open(BANDIT_FILE, "w", encoding='utf-8') as bandit_file:
        json.dump(bandit_badge, bandit_file)
    with open(RANDON_CC_FILE, "w", encoding='utf-8') as radon_cc_file:
        json.dump(radon_cc_badge, radon_cc_file)
    with open(RADON_LOC_FILE, "w", encoding='utf-8') as radon_loc_file:
        json.dump(radon_loc_badge, radon_loc_file)
    with open(PROSPECTOR_MSG_COUNT_FILE, "w", encoding='utf-8') as prospector_msg_count_file:
        json.dump(prospector_msgs_badge, prospector_msg_count_file)


def _prospector_msg_ratio_color(msg_count_ratio):
    if float(msg_count_ratio) > 20:
        return BADGE_COLORS[0]
    elif float(msg_count_ratio) > 10:
        return BADGE_COLORS[1]
    elif float(msg_count_ratio) > 5:
        return BADGE_COLORS[2]
    elif float(msg_count_ratio) > 1:
        return BADGE_COLORS[3]
    else:
        return BADGE_COLORS[4]


def _bandit_badge_color(severe_hits: int):
    if float(severe_hits) > 5:
        return BADGE_COLORS[0]
    elif float(severe_hits) > 3:
        return BADGE_COLORS[2]
    else:
        return BADGE_COLORS[4]

def _pylint_badge_color(pylint_score):
    if float(pylint_score) < 6:
        return BADGE_COLORS[0]
    elif float(pylint_score) < 7:
        return BADGE_COLORS[1]
    elif float(pylint_score) < 8:
        return BADGE_COLORS[2]
    elif float(pylint_score) < 9:
        return BADGE_COLORS[3]
    else:
        return BADGE_COLORS[4]


def _radon_cc_color(cc_score: float):
    if float(cc_score) >= 31:
        return BADGE_COLORS[0]
    elif float(cc_score) >= 21:
        return BADGE_COLORS[1]
    elif float(cc_score) >= 11:
        return BADGE_COLORS[2]
    elif float(cc_score) >= 6:
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
    parser.add_argument("bandit_sev_hits", type=int, help="Number of bandit severe hits (e.g., 10)")
    parser.add_argument("radon_cc", type=float, help="Radon cyclomatic complexity (e.g., 2.8)")
    parser.add_argument("radon_loc", type=int, help="Radon LOC (e.g., 3830)")
    parser.add_argument("prospector_msgs", type=int, help="Count of prospector messages (e.g., 7)")
    args = parser.parse_args()

    write_json_files(str(args.coverage_percentage), str(args.pylint_score), str(args.bandit_sev_hits),
                     str(args.radon_cc), str(args.radon_loc), str(args.prospector_msgs))
