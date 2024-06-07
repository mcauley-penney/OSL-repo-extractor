# OSL Repo Extractor
The extraction stage of the NAU-OSL project pipeline.


## Purpose
The GitHub Repo Extractor provides an expedient way to gather data from GitHub repositories using the [GitHub REST API](https://docs.github.com/en/rest). See the documentation for more information.


## Requirements

This project uses [Poetry](https://python-poetry.org) to manage its dependencies. To get started,

1. install the correct version of Python, listed in `pyproject.toml`. Try [pyenv](https://github.com/pyenv/pyenv)!
1. install [Poetry](https://github.com/python-poetry/poetry)
1. run `poetry install` to install dependencies
1. run `poetry run python main.py <input_file>` to run the program (see docs for input information)

## Contributing
#### commit formatting
- Please abide by the ["Conventional Commits"](https://www.conventionalcommits.org) specification for all commits

#### source code standards
Using default settings for each, please:
- format all contributions with [black](https://pypi.org/project/black/)
    - `pip install black`
- lint all contributions with [pylint](https://pypi.org/project/pylint/)
    - `pip install pylint`
