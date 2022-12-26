Author: Jacob McAuley Penney <jacobmpenney@gmail.com>

# User's Guide
- [Version](https://semver.org/) `1.0`


## Table of Contents
1. [Requirements](#requirements)
2. [Getting started quickly](#quick-start)
3. [Purpose](#purpose)
4. [Usage Instructions](#how-to-use)
    1. [Configuration options](#configuration-options)


## Introduction
This user guide attempts to be as high-level and technology-agnostic as it can be. This means that it will allude to various technologies, such as languages, libraries, or file extension types, only when it is necessary for the user to have that information.


## Requirements
1. Python 3.8.3 or greater
    - `🚩 Attention:` see the [gotchas file](./gotchas.md) for known issues when using a Python version other than 3.8.3
2. All required libraries
    - to see all required libraries, view `requirements.txt`
    - to install all required libraries, issue `$pip install -r requirements.txt`
3. A GitHub account and a GitHub Personal Access Token with `repo:status` and `public_repo` permissions


## Quick Start
To begin mining, have a GitHub use `python` to call the extractor and pass an input JSON to it:

`$python extractor_driver.py <path_to_input.json>`

An example call, where one's `pwd` is the root of the project and where you are using the provided example input, would be:

`$python extractor_driver.py ./docs/user/example_io/facebook-react_example_input.json`

`⚠️ Warning:`
1. If you use the example input to start, be sure to change the relevant paths, especially the output path, to real, safe paths in your file system before you get started with it. The extractor *will* create or overwrite files in your file system.
2. Read on below for information on the various configuration options.


## Purpose
The extractor is used to programmatically mine data from the GitHub Rest API v3 which is relevant to the NAU-OSL project pipeline. If you are working on this project and need to gather inputs from GitHub to pass to the rest of the pipeline, this project can help you.


## Usage Instructions
The extractor was built and tested with command line operation in mind and working with it from the command line is advised.  See the above `Quick Start` Guide for information on how to run it.

The driver function for the extractor requires a configuration file as an argument. This configuration file currently must contain a JSON object and must have certain fields. The extractor uses JSON schema validation to ensure that those fields exist, so it will warn you and stop execution if it finds that one of them is missing.

### Configuration options
Please see the [dedicated configuration options file](./configuration_opts.md) for full details.
