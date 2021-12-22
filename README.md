# OSL Repo Extractor

The initial stage of [Fabio Marcos'](https://github.com/fabiojavamarcos) NAU-OSL project pipeline.
See the [changelog](./CHANGELOG.md) for updates.

## Usage

### arguments

```shell
$ python main.py
usage: main.py [-h] extractor_cfg_file
main.py: error: the following arguments are required: extractor_cfg_file
```

The extractor requires only a path to a configuration file. The sample configuration at
`repo-extractor/data/input/configs/sample.json` is a good place to start experimenting. The extractor will report to you
what keys are missing, if any, and whether the values for those keys are acceptable. An acceptable call from the command line
will look like:

```shell
$ python main.py <path/to/cfg/file>
```


### configuration

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
        "pr_body",
        "pr_title"
    ]
}
```

Some key points about the configuration:

- The `auth_file` value requires a path to a file containing a GitHub Personal Access Token. Please format the PAT with no
  extra newlines or trailing spaces. The PAT should be on the first line.

- The `output_dir` will be used to create the necessary outputs for you using the provided repo. You do not need to provide
  a name to an output file nor do you need to create the output directory by hand; it will be created for you if it does not
  exist.  After an execution, the output directory structure will look like:

                                <output_dir>/<repo>/<repo>_output.JSON
                                                 e.g.
                                <output_dir>/jabref/jabref_output.JSON

- <span id="range">The `range` value discusses the actual item numbers you want to gather data from. If you want data from
  PR #270 up to PR #280 in a given repository, give [270, 280] to the range key, as above. The range behaves [x, y),
  gathering the first item in the range but excluding the second value.</span>

- The `fields` keys discuss what pieces of data you want to gather from the objects in the given range. The extractor will
  merge gathered data. For example, if you collected the `pr_body` for objects 1-10 but wanted to gather the `issue_username`
  for those same objects, you can simply change the values of the `fields` keys and run again. The extractor will simply add
  the new data in for each key in the JSON output.
    - You do not need to ask for issue numbers, PR numbers, the PR's merged status. Those pieces of data are mandatory, will
      always be collected, and the commands to access them are private.


### output

During a round of API calls, the extractor will compile gathered outputs into a dictionary. Under two conditions, the
extractor will write output to the output file provided in the configuration:

1. before sleeping when rate-limited by the GitHub REST API
2. after finishing gathering all the data for a range

This means that data will be collected even when the program does not completely finish.

The output produced by the extractor is pretty-printed JSON. Because it is printed in a human-readable format, it is very
easy to see what the extractor has collected and where the program left off in the case that you must stop it.
See the example output at `data/output/jabref/jabref_output.JSON`.

The human-readable output paired with the [range functionality](#range) discussed above conveniently allows the user to
start and stop at will. For example, you may be collecting data from a very large range but must stop for some reason.
You can look at the output, see what PR or issue number the extractor last collected data for, and use that as the
starting value in your range during your next execution.


### troubleshooting

If you are having an issue running the extractor, such as Python reporting that the `v2` package does not exists, you likely
need to update your `PYTHONPATH` environment variable. To do this, you can use the command below with modifications;
substitute the path in quotes with the path to the `extractor` subdir inside of the project, i.e.
`/home/<user>/<rest_of_path>/GitHub-Repo-Extractor/extractor` and the redirect location with the path to your shell rc file,
e.g. `~/.bashrc` or `~/.zshrc`:

```shell
$ echo 'export PYTHONPATH="<path_to_extractor>"' >> <shell_rcfile_location>
```


## Contributing
Using default settings for each, please:
- format all contributions with [black](https://pypi.org/project/black/)
    - `pip install black`
- lint all contributions with [pylint](https://pypi.org/project/pylint/)
    - `pip install pylint`


## Requirements
- Written in `Python 3.9.9` and `3.10.1`
- Packages:
    - [PyGithub](https://pygithub.readthedocs.io/en/latest/introduction.html)
        - `pip install pygithub`
    - [Cerberus](https://pygithub.readthedocs.io/en/latest/introduction.html)
        - `pip install cerberus`
