# OSL Repo Extractor

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7571311.svg)](https://doi.org/10.5281/zenodo.7571311)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7740450.svg)](https://doi.org/10.5281/zenodo.7740450)

The GitHub Repo Extractor provides an expedient way to gather issue and PR data from GitHub repositories using the [GitHub REST API](https://docs.github.com/en/rest). See this repo's documentation for more information.

## Requirements

This project uses [Poetry](https://python-poetry.org) to manage its dependencies. To get started,

1. install the correct version of Python, listed in `pyproject.toml`. Try [pyenv](https://github.com/pyenv/pyenv)!
1. install [Poetry](https://github.com/python-poetry/poetry)
1. run `poetry install` to install dependencies
1. run `poetry run python main.py <input_file>` to run the program (see docs for input information)

## Contributing

- Abide by the ["Conventional Commits"](https://www.conventionalcommits.org) specification for all commits.
- Using default settings for each, format and lint all Python contributions with [black](https://pypi.org/project/black/) and [pylint](https://pypi.org/project/pylint/) respectively.
