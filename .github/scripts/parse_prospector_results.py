"""
Parse the JSON output from prospector
"""
import json


def _parse_prospector_file(prospector_json):
    with open(prospector_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['summary']['message_count']


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse prospector json output")
    parser.add_argument("prospector_json", type=str, help="Prospector json output file")
    args = parser.parse_args()

    if args.prospector_json:
        msg_count = _parse_prospector_file(args.prospector_json)
        print(msg_count)
