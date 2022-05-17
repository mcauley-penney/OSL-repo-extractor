# TODO:

1. add visuals for:
    • the pipeline

2. update configuration and usage info
    • provide internal links to items and just avoid giving paths
        • paths keep changing, just avoid them dummy

3. after migrating to pdoc, host external API stuff on GitHub Pages



====================================================================

Author: Jacob McAuley Penney <jacobmpenney@gmail.com>


### Introduction
The purpose of this document is to serve as an introduction to this program in the context of the parent project and to act as an entryway for those who may be contributing or maintaining it in the future. Accordingly, it provides a discussion of its purpose and general structure. Before contacting the author with questions, please read and understand the contents below.

The OSL Repo Extractor ("extractor") is a tool used to mine GitHub repositories for information relevant to the total OSL project led by [Fabio Marcos De Abreu Santos](https://github.com/fabiojavamarcos) and under the supervision and direction of [Dr. Marco Gerosa](https://www.ime.usp.br/~gerosa/career.html). It is the first stage of the pipeline of the project, feeding the rest of it the data that it needs.


### Context and Purpose
The goal of the OSL project is to create predictive labels which discuss the skills required by developers to successfully solve open issues on GitHub. For example, if a particular issue requires that a developer have skill with a particular API, this project would like to discern that fact and label the issue accordingly. The intent is to make it easier for open source projects to get and retain contributors and for contributors to have an easier time contributing.

The project aims to do this by gathering data from issues that have been solved in the past, analyzing the libraries used in the commits which contributed to solving those issues, and applying that information to issues that have not yet been solved. This means the project is interested in three overarching types of data from GitHub: issues that have been solved and closed, the pull requests that contributed to solving them (meaning accepted and closed pull requests), and issues that are still open. Inside of those fields there are obviously subfields of data that are pertinent and useful. The extractor gathers all of this data for the rest of the project.


### Structure -- TODO: expand
The extractor employs singleton-like (soon to be properly singleton) classes which hold the various items needed to gather the data that we're after. In order, as of the time of this writing, one must initialize a configuration object and pass it to the extractor, which uses it to initialize a connection to GitHub and as a set of instructions on what pieces of data to gather.

[GitHub considers all pull requests as issues](https://docs.github.com/en/rest/issues/issues#list-issues-assigned-to-the-authenticated-user=). Given the three types of data that the project is interested in mentioned above, all data that the extractor is after can be gathered through a repository's list of issues.

To gather this data, the extractor employs [PyGithub](https://github.com/PyGithub/PyGithub) as a means of expediently interfacing with the GitHub REST API. The extractor is built around PyGithub's functionality


### Usage
#### arguments
```
$ python main.py
usage: main.py [-h] extractor_cfg_file
main.py: error: the following arguments are required: extractor_cfg_file
```

The extractor requires only a path to a configuration file. The sample configuration at
`./doc/example_extractor_cfg.json` is a good place to start experimenting. The extractor will report to you
what keys are missing, if any, and whether the values for the accepted keys are acceptable. An acceptable call
from the command line will look like:
```
$ python main.py <path/to/cfg/file>
```


#### configuration
Please see the extractor configuration template in `docs/example_io/` to get started.

Some key points about the configuration:

- The `auth_file` value requires a path to a file containing a GitHub Personal Access Token. Please format the PAT with no
  extra newlines or trailing spaces. The PAT should be on the first line.

- The `state` value is used to determine whether or not the extractor will gather data on PR's that are either
    1. open
    2. closed *and* merged

    The extractor will not look at PR's that are closed and not merged.

- The `range` value discusses the actual item numbers you want to gather data from. If you want data from PR #270 up to
  PR #280 in a given repository, give [270, 280] to the range key, as above. The range behaves [x, y]; it is inclusive of both values.

- The `fields` keys discuss what pieces of data you want to gather from the objects in the given range. The extractor will
  merge gathered data. If you collected one piece of data for a range of API items, e.g. the `body` of a set of PR's, but now want to collect the `title` of those same PR's, you can simply add the correct field, `title`, to the `pr_fields` list and the extractor will collect that data and merge it with the already existing JSON dictionary at the current output.

    - **You do not need to ask for:**
        - issue numbers
        - PR numbers
        - a PR's merged status

      Those pieces of data are mandatory when collecting data for those API item types, meaning that they will always be collected when collecting data on their respective item. *You do not need to attempt to provide them as arguments to the configuration file's "fields" lists.*


#### output
During a round of API calls, the extractor will compile gathered outputs into a dictionary. Under two conditions, the
extractor will write output to the output file provided in the configuration:

1. before sleeping when rate-limited by the GitHub REST API
2. after finishing gathering all the data for a range

This means that data will be collected even when the program does not completely finish.

The output produced by the extractor is pretty-printed JSON. Because it is printed in a human-readable format, it is very
easy to see what the extractor has collected and where the program left off in the case that you must stop it. See the
example output at `data/output/jabref/jabref_output.JSON`.

The human-readable output paired with the range functionality discussed above conveniently allows the user to start and stop
at will. For example, you may be collecting data from a very large range but must stop for some reason. You can look at the
output, see what PR or issue number the extractor last collected data for, and use that as the starting value in your range
during your next execution.


### Future Improvements

- enforce singleton pattern for the configuration and GitHub session classes
    - They are intended to be singletons but there is currently no mechanism to enforce that only a single instance may be created.

- implement a class to manage the various external connections, including the GitHub session but possibly also to Postgres
    - As of right now, the GitHub session is the only one necessary, but that may change in the future and this proposed session manager class would be a more fitting "main actor" than the extractor class. The extractor class would become more lower level than the GitHub session instance.

- use class and function decorators to improve coherence
    - for example, this project has some methods that really should belong to a class but were left out of that class because they did not require an instance of the object type. These methods could benefit from the `@static` decorator
