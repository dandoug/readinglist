import os
import zipfile
from pathlib import Path

# Define the name of the output zip file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ZIP_FILE = PROJECT_ROOT / "app_package.zip"

# Directories and files to exclude
EXCLUDE_PATTERNS = [
    ".DS_Store",
    "*.DS_Store",
    ".build/*",
    ".coverage*",
    ".env*",
    ".git/*",
    ".github/*",
    ".gitignore",
    ".idea",
    ".pytest*",
    ".secrets",
    ".venv/*",
    "*.pyc",
    "app_package.zip",
    "coverage.*",
    "database/*",
    "htmlcov/*",
    "pylint.*",
    "pytest.ini",
    "*README.md",
    "tests/*"
]


def package_app():
    """
    Package the application into a zip file, excluding specified files and directories.
    """
    print(f"Creating {ZIP_FILE}...")

    # Remove existing zip file if it exists
    if os.path.exists(ZIP_FILE):
        os.remove(ZIP_FILE)

    with zipfile.ZipFile(ZIP_FILE, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT, topdown=True):
            # Exclude directories from traversal
            dirs[:] = [d for d in dirs if not _should_exclude(os.path.join(root, d))]

            for file in files:
                file_path = os.path.join(root, file)
                # Skip excluded files
                if _should_exclude(file_path):
                    continue

                # Add file to the zip archive
                arcname = os.path.relpath(file_path, PROJECT_ROOT)
                zipf.write(file_path, arcname)
                print(f"Added: {arcname}")

    print(f"Package created: {ZIP_FILE}")


def _should_exclude(file_path):
    """
    Check if a file matches any of the exclude patterns.
    """
    from fnmatch import fnmatch
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch(file_path, PROJECT_ROOT / pattern):
            return True
    return False


if __name__ == "__main__":
    package_app()
