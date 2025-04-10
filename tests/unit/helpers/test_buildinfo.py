from app.helpers.buildinfo import BUILD_INFO_FILE
from app.helpers import check_and_generate_build_info
import json


def test_generate_build_info():
    _remove_build_info()

    check_and_generate_build_info()

    build_info = _read_build_info()
    assert "commit_id" in build_info
    assert "commit_id" is not ""

    lmd = _get_build_info_last_modified()

    # should not change
    check_and_generate_build_info()

    assert lmd == _get_build_info_last_modified()

    _write_old_build_info()

    check_and_generate_build_info()
    build_info = _read_build_info()
    assert "commit_id" in build_info
    assert "commit_id" is not ""

    _write_empty_build_info()

    check_and_generate_build_info()
    build_info = _read_build_info()
    assert "commit_id" in build_info
    assert "commit_id" is not ""


def _read_build_info():
    assert BUILD_INFO_FILE.exists()
    build_info = json.loads(BUILD_INFO_FILE.read_text())
    assert isinstance(build_info, dict)
    return build_info


def _remove_build_info():
    # remove any existing file
    try:
        BUILD_INFO_FILE.unlink()
    except FileNotFoundError:
        pass


def _write_old_build_info():
    build_info = {
        "branch": "",
        "commit_id": "",
        "committer": "",
        "comment": "old_build",
        "build_date": "2024-04-10T13:49:15",
        "commit_date": "2024-04-10T13:49:15",
    }

    # Write to build-info.json file
    with open(BUILD_INFO_FILE, 'w') as f:
        json.dump(build_info, f, indent=4)

def _write_empty_build_info():
    build_info = {
        "branch": "",
        "commit_id": "",
        "committer": "",
        "comment": "",
        "build_date": "",
        "commit_date": "",
    }

    # Write to build-info.json file
    with open(BUILD_INFO_FILE, 'w') as f:
        json.dump(build_info, f, indent=4)

def _get_build_info_last_modified():
    return BUILD_INFO_FILE.stat().st_mtime
