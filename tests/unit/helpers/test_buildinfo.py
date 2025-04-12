import json
import logging

from app.helpers import (read_build_info, write_empty_build_info,
                         BUILD_INFO_FILE, buildinfo)
from dulwich.errors import NotGitRepository

from app.helpers.buildinfo import _get_commit_target_branch


def test_generate_build_info():
    from app.helpers import check_and_generate_build_info
    from app.helpers import remove_build_info
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


def test_check_and_generate_build_info_exceptions(mocker):
    write_empty_build_info()

    # Mock Repo to raise NotGitRepository
    mock_repo = mocker.patch('app.helpers.buildinfo.Repo', side_effect=NotGitRepository)
    from app.helpers import check_and_generate_build_info
    check_and_generate_build_info() # exception raised by caught
    assert mock_repo.called  # verify mocker was called
    mock_repo.reset_mock()


def test_remove_build_info(mocker):
    # Mock the unlink method of BUILD_INFO_FILE to raise FileNotFoundError
    mock_unlink = mocker.patch('app.helpers.buildinfo.Path.unlink',
                               side_effect=FileNotFoundError)
    from app.helpers.buildinfo import remove_build_info
    remove_build_info()
    mock_unlink.assert_called_once()
    mock_unlink.reset_mock()


def test_generate_build_info_exception(mocker):
    # Mock Repo to raise NotGitRepository
    mock_repo = mocker.patch('app.helpers.buildinfo.Repo', side_effect=NotGitRepository)
    from app.helpers.buildinfo import _generate_build_info
    _generate_build_info(None)  # exception raised by caught
    assert mock_repo.called  # verify mocker was called
    mock_repo.reset_mock()


def test_get_commit_target_branch_head_missing(mocker):
    # Mock the repo object
    mock_repo = mocker.Mock()
    mock_repo.refs = {b"HEAD": None}  # Simulate no HEAD exists
    result = _get_commit_target_branch(mock_repo)
    assert result == "(none)"


def test_get_commit_target_branch_on_branch(mocker):
    # Mock the repo object
    mock_repo = mocker.Mock()
    mock_repo.refs = {b"HEAD": b"refs/heads/main"}  # HEAD points to the main branch
    result = _get_commit_target_branch(mock_repo)
    assert result == "main"


def test_get_commit_target_branch_detached_no_tracking(mocker):
    # Mock the repo object
    mock_repo = mocker.Mock()
    mock_repo.refs = {
        b"HEAD": b"some-commit-id",  # Simulate a detached HEAD state
        b"refs/heads/main": b"some-other-commit-id",  # No branch matches HEAD commit
    }
    result = _get_commit_target_branch(mock_repo)
    assert result == "(detached)"


def test_get_commit_target_branch_detached_with_tracking(mocker):
    # Mock the repo object
    mock_repo = mocker.Mock()
    mock_repo.refs = {
        b"HEAD": b"some-commit-id",  # Simulate a detached HEAD state
        b"refs/heads/feature-branch": b"some-commit-id",  # HEAD commit matches this branch
    }
    result = _get_commit_target_branch(mock_repo)
    assert result == "feature-branch"


def test_get_commit_target_branch_with_exception(mocker, caplog):
    # Mock the repo object to raise an exception
    mock_repo = mocker.Mock()
    mock_repo.refs = {} # generates KeyError

    with caplog.at_level(logging.ERROR):
        result = _get_commit_target_branch(mock_repo)

    assert "(error: b'HEAD')" in result
    assert "An unexpected error occurred" in caplog.text


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
