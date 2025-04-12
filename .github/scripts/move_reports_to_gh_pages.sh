#!/usr/bin/env bash

# Get reference to project root directory
PROJECT_ROOT=$(dirname "$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")")

# Remove existing directory, /tmp/readinglist, and all its contents (if it exists)
if [ -d "/tmp/readinglist" ]; then
  rm -rf /tmp/readinglist
fi

# Clone the gh-page branch for repo with our pages source into a new directory under /tmp
git clone --branch gh-pages --single-branch https://x-access-token:${GITHUB_TOKEN}@github.com/dandoug/readinglist.git /tmp/readinglist

# Delete existing report files
find /tmp/readinglist/reports -type f -delete
find /tmp/readinglist/reports -type d -empty -delete

# Move the report files to /tmp/readinglist/reports
mkdir -p /tmp/readinglist/reports
REPORTS_TO_MOVE=("coverage.xml" "pylint.report.txt" "htmlcov" "coverage.json" "pylint.json" )
for REPORT in "${REPORTS_TO_MOVE[@]}"; do
  mv "$PROJECT_ROOT/$REPORT" /tmp/readinglist/reports/
done

# Don't let htmlcov keep a .gitignore file, prevents adding new coverage files
if [ -f "/tmp/readinglist/reports/htmlcov/.gitignore" ]; then
  rm /tmp/readinglist/reports/htmlcov/.gitignore
fi

# Stage and commit all the modified or added files in the /tmp/readinglist directory
(
  cd /tmp/readinglist && \
  git config user.name "github-actions[bot]" && \
  git config user.email "github-actions[bot]@users.noreply.github.com" && \
  git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/dandoug/readinglist.git && \
  git add . && \
  git commit -m "Update reports" && \
  git push origin gh-pages
)
  
# cleanup the /tmp/readinglist directory  
rm -rf /tmp/readinglist
