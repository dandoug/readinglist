from app.helpers import check_and_generate_build_info, read_build_info, write_empty_build_info, remove_build_info, BUILD_INFO_FILE
import json


def test_generate_build_info():
    remove_build_info()

    check_and_generate_build_info()

    build_info = read_build_info()
    assert "commit_id" in build_info
    assert "commit_id" is not ""

    lmd = _get_build_info_last_modified()

    # should not change
    check_and_generate_build_info()

    assert lmd == _get_build_info_last_modified()

    _write_old_build_info()

    check_and_generate_build_info()
    build_info = read_build_info()
    assert "commit_id" in build_info
    assert "commit_id" is not ""

    write_empty_build_info()

    check_and_generate_build_info()
    build_info = read_build_info()
    assert "commit_id" in build_info
    assert "commit_id" is not ""


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


def _get_build_info_last_modified():
    return BUILD_INFO_FILE.stat().st_mtime
