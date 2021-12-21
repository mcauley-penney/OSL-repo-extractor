# OSL Repo Extractor

The initial stage of [Fabio Marcos'](https://github.com/fabiojavamarcos) NAU-OSL project pipeline.
See the [changelog](./CHANGELOG.md) for updates.

## Usage

#### arguments

```shell
~/files/work/repo-extractor/extractor/v2
» python main.py
usage: main.py [-h] extractor_cfg_file [logging_destination]
main.py: error: the following arguments are required: extractor_cfg_file
```

The extractor requires a path to a configuration file and accepts an optional path to a directory to log output to. The
sample configuration at `repo-extractor/data/input/configs/sample.json` is a good place to start experimenting. The
extractor will report to you what keys are missing, if any, and whether the values and their types for those keys are
correct.

If no logging path is provided, the extractor will use `./extractor_logs`. In any case, the log file name will be created as
`extractor_log.txt`.


#### configuration

```shell
~/files/work/repo-extractor/data/input/configs
» cat sample.json
{
    "repo": "JabRef/jabref",
    "auth_file": "/home/m/files/work/repo-extractor/data/input/auths/mp_auth.txt",
    "output_dir": "/home/m/files/work/GitHub-Repo-Extractor-2/data/output",
    "range": [
        270,
        280
    ],
    "commit_fields": [
        "commit_author_name",
        "commit_date",
        "commit_message"
    ],
    "issues_fields": [
        "issue_username"
    ],
    "pr_fields": [
        "pr_merged",
        "pr_body",
        "pr_title"
    ]
}
```

Some key points about the configuration:

- The `auth_file` key requires a path to a file containing a GitHub Personal Access Token. Please format the PAT with no
  extra newlines or trailing spaces. The PAT should be on the first line.

- The `output_dir` will be used to create the necessary outputs for you using the provided repo. You do not need to provide
  a name to an output file nor do you need to create the output directory by hand; it will be created for you if it does not
  exist.  After an execution, the output directory structure will look like:

        <output_dir>/<repo>/<repo_output.JSON>

                        e.g.

        <output_dir>/jabref/jabref_output.JSON

- The `range` value discusses the actual item numbers you want to gather data from. If you want data from PR #270 up to
  PR #280 in a given repository, give [270, 280] to the range key, as above. The range behaves [x, y), gathering the first
  item in the range but excluding the second value.

- The `fields` keys discuss what pieces of data you want to gather from the objects in the given range. The extractor will
  merge gathered data. For example, if you collected the `pr_body` for objects 1-10 but wanted to gather the `issue_username`
  for those same objects, you can simply change the values of the `fields` keys and run again. The extractor will simply add
  the new data in for each key in the JSON output.
    - You do not need to ask for issue numbers, PR numbers, or whether the PR is merged. Those pieces of data are mandatory,
      will always be collected, and the commands to access them are private.

## Contributing
Using default settings, please:
- format all contributions with [black](https://pypi.org/project/black/)
    - `pip install black`
- lint all contributions with [pylint](https://pypi.org/project/pylint/)
    - `pip install pylint`


## Requirements
- Written in Python 3.9.9 and 3.10.1
- Packages:
    - [PyGithub](https://pygithub.readthedocs.io/en/latest/introduction.html)
        - `pip install pygithub`
    - [Cerberus](https://pygithub.readthedocs.io/en/latest/introduction.html)
        - `pip install cerberus`
