---
title: Development
nav_order: 3
---
# Development

...rough outline and notes, [backlog item](https://github.com/dandoug/readinglist/issues/62) to refine is pending...

## Installation of requisite tools

* **homebrew**, the start of so many journeys
  * installed via [instructions](https://docs.brew.sh/Installation)
* **python 3.11**
  * installed `pyenv` via `homebrew`, instealled python 3.11 via pyenv 
* **docker**, for running tests
  * installed via [download](https://docs.docker.com/get-started/get-docker/)
* **act**, for running GitHub Action pipeline
  * v0.2.76 installed via `homebrew`
* **mysql** database, for dev/testing
  * installed v9.2 via `homebrew`, v8.4.4 used in prod 
* **mysql workbench**, used for db setup and operations
  * installed via [download](https://dev.mysql.com/downloads/workbench/)  
* **ruby**, for building/testing ghpages docs 
  * installed `rbenv` via `homebrew`, installed ruby 3.2.8 via rbenv

## Project Source structure

**Source:** [https://github.com/dandoug/readinglist](https://github.com/dandoug/readinglist)

**Branches:**
* _main_ - branch for code 
  * create code development branches based from here
* _gh-pages_ - branch for doc
  * create documentation branches from here

Use [PRs](https://github.com/dandoug/readinglist/pulls) to get work merged.

## Project tracking

* Tracked as [project on github](https://github.com/users/dandoug/projects/1)

## Deployment

### AWS Elastic Beanstalk configuration

### SSL Certificate Generation

### Secrets

## Testing

### Running integration tests locally

### Running Github Action pipeline locally

```bash
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest --env-file "testing/integration/.env.testing" --secret-file .secrets
```

### Running Jekyll locally
To test docs locally
```bash
bundle exec jekyll serve --config "_config.yml,_config_dev.yml"
```


## Development metrics
![Pylint Score](https://img.shields.io/endpoint?style=for-the-badge&url=https://docs.booklist.media/reports/pylint.json)&nbsp;&nbsp;&nbsp;![Test Line Coverage](https://img.shields.io/endpoint?style=for-the-badge&url=https://docs.booklist.media/reports/coverage.json)&nbsp;&nbsp;&nbsp;![Bandit Severe Hits](https://img.shields.io/endpoint?style=for-the-badge&url=https://docs.booklist.media/reports/bandit.json)
![Radon Cyclomatic Complexity](https://img.shields.io/endpoint?style=for-the-badge&url=https://docs.booklist.media/reports/radon_cc.json)&nbsp;&nbsp;&nbsp;![Radon LOC](https://img.shields.io/endpoint?style=for-the-badge&url=https://docs.booklist.media/reports/radon_loc.json)&nbsp;&nbsp;&nbsp;![Prospector Message ratio](https://img.shields.io/endpoint?style=for-the-badge&url=https://docs.booklist.media/reports/prospector_msg_count.json)

### Pylint

* [pylint report](reports/pylint.report.txt)


### Pytest

* [coverage.xml](reports/coverage.xml)
* [coverage html report](reports/htmlcov/index.html)

### Bandit

* [bandit json report](reports/bandit_output.json)
* [bandit html report](reports/bandit_output.html)

### Radon

* [Radon CC report](reports/radon_cc_report.txt)
* [Radon RAW report](reports/radon_raw_report.txt)

### Prospector

* [Prospector report](reports/prospector.json)