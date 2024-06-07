# User's Guide

## Introduction

This user guide attempts to be high-level and technology-agnostic. This means that it will allude to various technologies, such as languages, libraries, or file extension types, only when it is necessary for the user to have that information.

If you are working on this project and need to gather inputs from GitHub to pass to the rest of the pipeline, this tool can help you.

## Requirements

1. Python 3.11.9
   - `🚩 Attention:` see the [gotchas file](./gotchas.md) for known issues when using a Python version other than 3.8.3
1. All required libraries
   - to see all required libraries, view `requirements.txt`
   - to install all required libraries, issue `$pip install -r requirements.txt`
1. A GitHub account and a GitHub Personal Access Token with `repo:status` and `public_repo` permissions

## Usage Instructions

The extractor was built and tested for command line operation.

### Arguments

The driver function for the extractor requires only a configuration file as an argument:

```
$ python main.py
usage: main.py [-h] extractor_cfg_file
main.py: error: the following arguments are required: extractor_cfg_file
```

This configuration file must contain a JSON object with certain fields. The extractor uses JSON schema validation to ensure that those fields exist, so it will warn you and stop execution if it finds that one of them is missing.

The user may find an example input in this directory at `./example_io/example_input.json`. Please see the [dedicated configuration options file](./configuration_opts.md) for full details on the options one may pass to the extractor inside of the JSON input object.

### Execution

To begin mining, use `python` to call the extractor and pass an input JSON to it:

`$ python main.py <path/to/cfg/file.json>`

An example call, in which one's `pwd` is the root of the project and where you are using the provided example input, would be:

`$ python main.py ./docs/user/example_io/facebook-react_example_input.json`

`⚠️ Warning:` If you use the example input to start, be sure to change the relevant paths, especially the output path, to real, safe paths in your file system **before** you execute the program. The extractor *will* create or overwrite files in your file system.

### Output

During a round of API calls, the extractor will compile gathered outputs into a dictionary. Under two conditions, the
extractor will write output to the output file provided in the configuration:

1. before sleeping when rate-limited by the GitHub REST API
1. after finishing gathering all the data for a range

This means that data will be collected even when the program experiences an error or otherwise does not completely finish.

The output produced by the extractor is pretty-printed JSON. Because it is returned in a human-readable format, it is
easy to see what the extractor has collected and where the program left off in the case that you must resume execution. See the [example output](./example_io/example_output.json) for more.

The human-readable output paired with the range functionality provided by the configuration conveniently allows the user to start and stop at will. For example, you may be collecting data from a very large range but must stop for some reason. You can look at the output, see what issue number the extractor last collected data for, and use that as the starting value in your range during your next execution.
