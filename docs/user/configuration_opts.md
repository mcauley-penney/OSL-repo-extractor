# Configuration Options

## Introduction

Following are descriptions of the currently available configuration options. Please have the [example configuration](./example_io/example_input.json) open as you read the below information. Because the configuration JSON object is treated as a Python dictionary, the entries in the configuration may be in any order. They are given below in the order of the example input.

## Notes

`🚩 Attention:` Below are things you should know using and modifying this program

1. You do not need to ask for:
   - issue numbers
   - whether an issue is also a PR
   - the state of the given PR
   - a PR's merged status
   - the number of review comments a PR has

These points are required because the project needs them. They will be gathered for every issue you mine without asking.

2.  To GitHub, all PRs are issues, but not all issues are PRs. When gathering PRs, they are first mined as issues (meaning from the issues endpoints) then checked to see if they are also PRs. This information is relevant to understanding certain options below, such as `state`, and how the possible fields options, such as `issues` and `comments`, work.

## Options

- Name: repo
  - Required: true
  - Type: string
  - Description: The repo option must be in the form `repo_owner/repo_name`, exactly as shown in a GitHub repository’s URL or page title.
  - Possible Values: Any GitHub repository that the provided Personal Access Token (PAT) can access.
  - Notes: —
- Name: auth_path
  - Required: true
  - Type: string
  - Description: Path to a file containing a GitHub PAT. The token must be on the first line with no extra newlines or trailing spaces.
  - Possible Values: Any valid file-system path.
  - Notes: The PAT needs the proper scopes (e.g., `repo:status`, `public_repo` for classic tokens).
- Name: state
  - Required: true
  - Type: string
  - Description: Determines which pull-request state to mine. Closed + merged PRs are used for ML training; open PRs are used for the tool’s runtime tasks.
  - Possible Values: `open` or `closed` (`closed` mines only PRs that are both closed and merged).
  - Notes: PRs that are closed but not merged are ignored.
- Name: labels
  - Required: true
  - Type: list of strings
  - Description: Labels act as filters to the functionality that gathers issues to be mined. It is essentially a list of strings to filter issues on. If you want to mine comment data for all issues that are labeled as "bug", for example, you would have `["bug"]` as your `labels` input and then list the comment data you want in the `comments` configuration value.
  - Possible Values: any
  - Notes: -
- Name: range
  - Required: true
  - Type: list of integers
  - Description: Inclusive start–end numbers in a repo’s PR history to gather.
  - Possible Values: Both numbers ≥ 1. Example `[1, 10]` collects PR #1 through #10; `[1, 9]` stops before #10.
  - Notes: —
- Name: comments
  - Required: false
  - Type: list of strings
  - Description: Data points to mine from issue comments.
  - Possible Values: `body`, `userid`, `userlogin`.
  - Notes: May be an empty list if no comment data are needed. (See `repo_extractor/schema.py > cmd_tbl` for the authoritative list.)
- Name: commits
  - Required: false
  - Type: list of strings
  - Description: Data points to mine from commits associated with PRs.
  - Possible Values: `author_name`, `committer`, `date`, `files`, `message`, `sha`.
  - Notes: Gathered only for issues that are PRs. May be an empty list. (See `repo_extractor/schema.py > cmd_tbl`.)
- Name: issues
  - Required: false
  - Type: list of strings
  - Description: Data points to mine from issue metadata.
  - Possible Values: `body`, `closed_at`, `created_at`, `num_comments`, `title`, `userid`, `userlogin`.
  - Notes: Gathered only for issues that are also PRs (commits are irrelevant to stand-alone issues). May be an empty list. (See `repo_extractor/schema.py > cmd_tbl`.)
