"""
This module handles the generation and management of a `build-info.json` file, which stores
metadata about the current build and Git repository. It includes functionality to check,
generate, read, remove, and write build metadata based on the repository's state.
"""
import logging
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from dulwich.repo import Repo
from dulwich.errors import NotGitRepository


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_INFO_FILE = PROJECT_ROOT / "build-info.json"


def check_and_generate_build_info():
    """
    Checks if the file `build-info.json` exists and regenerates it if necessary. The function 
    compares timestamps between the last build and the latest commit to determine if 
    regeneration is needed.
    """

    if os.path.isfile(BUILD_INFO_FILE):
        logging.debug("%s exists. Checking timestamps...", BUILD_INFO_FILE)

        try:
            # Load the existing `build-info.json` file into memory
            with open(BUILD_INFO_FILE, 'r', encoding='utf-8') as f:
                existing_build_info = json.load(f)

            existing_commit_date = existing_build_info.get("commit_date", "")

            # Open the repository
            repo = Repo(PROJECT_ROOT)

            # Get the latest commit details
            head_ref = repo.head()
            latest_commit = repo[head_ref]
            latest_commit_date = datetime.fromtimestamp(latest_commit.commit_time).isoformat()

            # Compare timestamps
            if existing_commit_date:
                existing_timestamp = (datetime.fromisoformat(existing_commit_date)
                                      .replace(tzinfo=timezone.utc))
                latest_timestamp = (datetime.fromisoformat(latest_commit_date)
                                    .replace(tzinfo=timezone.utc))

                if latest_timestamp > existing_timestamp:
                    logging.debug(
                        "Latest commit is newer than the one in %s. "
                        "Regenerating the build-info.json file...", BUILD_INFO_FILE
                    )
                    _generate_build_info(repo)
                else:
                    logging.debug("%s is up-to-date.", BUILD_INFO_FILE)
            else:
                logging.debug("Existing commit date is invalid. Regenerating...")
                _generate_build_info(repo)

        except NotGitRepository:
            logging.warning("Git repository not found. Leaving existing build-info.json untouched.")

    else:
        logging.debug("%s does not exist. Generating a new one...", BUILD_INFO_FILE)
        _generate_build_info()


def read_build_info() -> dict:
    """
    Reads and parses the build information from a predefined file.

    This function ensures that the predefined build information file
    exists and is in valid JSON format. The file is read into a Python
    dictionary, which is then validated and returned.

    :return: A dictionary containing the build information read from the
        specified file.
    :rtype: dict
    :raises AssertionError: If the build information file does not exist.
    :raises AssertionError: If the parsed data is not a dictionary.
    """
    assert BUILD_INFO_FILE.exists()
    build_info = json.loads(BUILD_INFO_FILE.read_text())
    assert isinstance(build_info, dict)
    return build_info


def write_empty_build_info():
    """
    Writes an empty build information dictionary to a JSON file named `build-info.json`.

    The function initializes a dictionary with keys for branch name, commit ID,
    committer, comment, build date, and commit date. It assigns an empty string
    to each of these keys. The dictionary is then serialized and written to a
    JSON file with a filename specified by the constant `BUILD_INFO_FILE`.

    :raises FileNotFoundError: Raised if the specified file path does not exist
        or cannot be accessed for writing.
    """
    build_info = {
        "branch": "",
        "commit_id": "",
        "committer": "",
        "comment": "",
        "build_date": "",
        "commit_date": "",
    }
    # Write to build-info.json file
    with open(BUILD_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(build_info, f, indent=4)


def remove_build_info():
    """
    Removes the build information file if it exists. If the file does not exist,
    the operation gracefully handles the absence without raising an exception.

    :raises FileNotFoundError: Raised internally but handled by the function
                               when the file does not exist.
    """
    # remove any existing file
    try:
        BUILD_INFO_FILE.unlink()
    except FileNotFoundError:
        pass


def _generate_build_info(repo: Repo = None):
    """
    Generates a `build-info.json` file containing metadata from the Git repository if it 
    is available. If the repository is not found, default values are used instead. The 
    generated file includes details such as the branch name, commit ID, committer, comment, 
    build date, and commit date.
    """
    build_date = datetime.now(timezone.utc).isoformat()  # Build date in UTC

    try:
        # Open the repository, if not passed in
        if not repo:
            repo = Repo(PROJECT_ROOT)

        # Get the latest commit details
        head_ref = repo.head()

        commit = repo[head_ref]
        commit_id = commit.id.decode()
        committer = commit.committer.decode()
        comment = commit.message.decode().strip()
        commit_date = datetime.fromtimestamp(commit.commit_time, timezone.utc).isoformat()
        branch = _get_commit_target_branch(repo)

        build_info = {
            "branch": branch,
            "commit_id": commit_id,
            "committer": committer,
            "comment": comment,
            "build_date": build_date,
            "commit_date": commit_date,
        }

    except NotGitRepository:
        # Fallback logic if the Git repository is not initialized or unavailable
        logging.warning("Git repository not found. Using default values.")
        build_info = {
            "branch": "",
            "commit_id": "",
            "committer": "",
            "comment": "",
            "build_date": build_date,
            "commit_date": "",
        }

    # Write to build-info.json file
    with open(BUILD_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(build_info, f, indent=4)
    logging.debug("Generated %s successfully.", BUILD_INFO_FILE)


def _get_commit_target_branch(repo: Repo) -> str:
    """
    Determines the branch that would receive the next commit in the current repository. 
    If the repository is in a detached `HEAD` state, attempts to identify the branch that 
    tracks the current commit, if any.
    """
    try:
        # Read the HEAD reference
        head_ref = repo.refs[b"HEAD"]

        if not head_ref:
            return "(none)"  # No HEAD exists

        # If HEAD points to a branch, extract the branch name
        if head_ref.startswith(b"refs/heads/"):
            return head_ref.decode("utf-8")[len("refs/heads/"):]  # Current branch name

        # If HEAD does not point to a branch, we are in a detached HEAD state.
        # Check for the branch containing the current HEAD commit.
        head_commit = head_ref

        # Iterate through all refs to find the branch tracking the HEAD commit
        for ref in repo.refs:  # repo.refs supports iteration over keys
            if ref.startswith(b"refs/heads/"):  # Only check local branches
                if repo.refs[ref] == head_commit:  # Check if the commit matches
                    return ref.decode("utf-8")[len("refs/heads/"):]  # Extract branch name

        # No branch found tracking the current commit, or the repository is detached
        # without any tracking information
        return "(detached)"
    except Exception as e:  # pylint: disable=broad-except
        logging.error("An unexpected error occurred: %s", e, exc_info=True)
        return f"(error: {e})"


__all__ = ["check_and_generate_build_info", "read_build_info", "write_empty_build_info",
           "remove_build_info", "BUILD_INFO_FILE", "PROJECT_ROOT"]

if __name__ == "__main__":
    check_and_generate_build_info()
