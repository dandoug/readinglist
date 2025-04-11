import logging
import os
import json
from datetime import datetime, timezone
from dulwich.repo import Repo
from dulwich.errors import NotGitRepository
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUILD_INFO_FILE = PROJECT_ROOT / "build-info.json"


def check_and_generate_build_info():
    """
    Checks if build-info.json exists and handles regeneration logic based on timestamps.
    """

    if os.path.isfile(BUILD_INFO_FILE):
        logging.debug(f"{BUILD_INFO_FILE} exists. Checking timestamps...")

        try:
            # Load existing build-info.json file
            with open(BUILD_INFO_FILE, 'r') as f:
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
                existing_timestamp = datetime.fromisoformat(existing_commit_date).replace(tzinfo=timezone.utc)
                latest_timestamp = datetime.fromisoformat(latest_commit_date).replace(tzinfo=timezone.utc)

                if latest_timestamp > existing_timestamp:
                    logging.debug(f"Latest commit is newer than the one in {BUILD_INFO_FILE}. Regenerating...")
                    _generate_build_info(repo)
                else:
                    logging.debug(f"{BUILD_INFO_FILE} is up-to-date.")
            else:
                logging.debug("Existing commit date is invalid. Regenerating...")
                _generate_build_info(repo)

        except NotGitRepository:
            logging.warning("Git repository not found. Leaving existing build-info.json untouched.")

    else:
        logging.debug(f"{BUILD_INFO_FILE} does not exist. Generating a new one...")
        _generate_build_info()


def read_build_info() -> dict:
    assert BUILD_INFO_FILE.exists()
    build_info = json.loads(BUILD_INFO_FILE.read_text())
    assert isinstance(build_info, dict)
    return build_info


def write_empty_build_info():
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


def remove_build_info():
    # remove any existing file
    try:
        BUILD_INFO_FILE.unlink()
    except FileNotFoundError:
        pass


def _generate_build_info(repo: Repo = None):
    """
    Generates a build-info.json file with Git metadata if available, or default values if Git is unavailable.
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
        # Fallback if Git repository is not initialized or unavailable
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
    with open(BUILD_INFO_FILE, 'w') as f:
        json.dump(build_info, f, indent=4)
    logging.debug(f"Generated {BUILD_INFO_FILE} successfully.")


def _get_commit_target_branch(repo: Repo) -> str:
    """
    Determines the branch that would receive the next commit in the current repository.
    If the HEAD is detached, it finds the branch tracking the current commit (if any).
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

        # No branch found tracking the current commit or repo is detached without tracking
        return "(detached)"
    except Exception as e:
        return f"(error: {e})"


__all__ = ["check_and_generate_build_info", "read_build_info", "write_empty_build_info",
           "remove_build_info", "BUILD_INFO_FILE"]

if __name__ == "__main__":
    check_and_generate_build_info()
