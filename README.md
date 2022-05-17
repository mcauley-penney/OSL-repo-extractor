# OSL Repo Extractor
The extraction stage of the NAU-OSL project pipeline.


## Purpose
The GitHub Repo Extractor provides an expedient way to gather data from GitHub repositories using the [GitHub REST API](https://docs.github.com/en/rest). See the documentation for more information.


## Requirements
- Written in `Python 3.8.3`
- Install library dependencies via `requirments.txt` or manually
    - `pip install -r requirements.txt`
    - Packages:
        - [PyGithub](https://pygithub.readthedocs.io/en/latest/introduction.html)
            - `pip install pygithub`
        - [Cerberus](https://docs.python-cerberus.org/en/stable/)
            - `pip install cerberus`


## Contributing
#### commit formatting
- Please abide by the ["Conventional Commits"](https://www.conventionalcommits.org) specification for all commits

#### source code standards
Using default settings for each, please:
- format all contributions with [black](https://pypi.org/project/black/)
    - `pip install black`
- lint all contributions with [pylint](https://pypi.org/project/pylint/)
    - `pip install pylint`
