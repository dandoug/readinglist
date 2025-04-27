"""
Parse the JSON output from bandit and print out the number of high-severity issues found
"""
import json
import sys


def main():
    """
    Parse the json-formated output from bandit
    :return:
    """
    if len(sys.argv) != 2:
        print("Please provide the path to the JSON file as an argument")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as file:
            data = json.load(file)

        high_severity = data.get('metrics', {}).get('_totals', {}).get('SEVERITY.HIGH', 0)
        print(high_severity)

    except FileNotFoundError:
        print("File not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Invalid JSON file")
        sys.exit(1)


if __name__ == '__main__':
    main()
