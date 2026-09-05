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
  - Required: true within each target
  - Type: string
  - Description: Repository to mine, in the form `repo_owner/repo_name`, exactly as shown in its GitHub URL.
  - Possible Values: Any GitHub repository that the provided Personal Access Token (PAT) can access.
  - Notes: Repository names belong in `targets`, not in the top-level `fields` object.
- Name: auth_path
  - Required: true
  - Type: string
  - Description: Path to a file containing a GitHub PAT. The token must be on the first line with no extra newlines or trailing spaces.
  - Possible Values: Any valid file-system path.
  - Notes: The PAT needs the proper scopes (e.g., `repo:status`, `public_repo` for classic tokens).
- Name: output_path
  - Required: true
  - Type: string
  - Description: Path to the extracted data JSON document.
  - Possible Values: Any writable file-system path.
- Name: report_path
  - Required: false
  - Type: string
  - Description: Path to the extraction report JSON document.
  - Possible Values: Any writable file-system path.
  - Notes: If omitted, the report is written to `output_path` with `.report.json` appended.
- Name: state
  - Required: true within each target
  - Type: string
  - Description: Determines which pull-request state to mine. Closed + merged PRs are used for ML training; open PRs are used for the tool’s runtime tasks.
  - Possible Values: `open`, `closed`, or `all`.
  - Notes: State is configured independently for each target.
- Name: labels
  - Required: true within each target
  - Type: list of strings
  - Description: Labels act as filters to the functionality that gathers issues to be mined. It is essentially a list of strings to filter issues on. If you want to mine comment data for all issues that are labeled as "bug", for example, you would have `["bug"]` as your `labels` input and then list the comment data you want in the `comments` configuration value.
  - Possible Values: any
  - Notes: Labels are configured independently for each target.
- Name: fields
  - Required: true
  - Type: object
  - Description: Shared issue, conversation-comment, review-comment, review, and commit field selections applied to every target unless overridden.
  - Notes: Field selectors such as `issues` and `comments` live directly in this object. Targets may replace individual field lists with their own `fields` object.
- Name: targets
  - Required: true
  - Type: list of objects
  - Description: Repositories to mine. Each target supplies a `repo`, `range`, `state`, and `labels`, and may override individual field lists.
  - Notes: A range is a list containing issue numbers and one-level nested inclusive ranges. For example, `[1, [5, 8], 19]` selects issues 1, 5, 6, 7, 8, and 19. `[[1, -1]]` selects every issue through the latest issue in the repository. Overlapping selectors are ignored naturally and do not cause duplicate extraction.
- Name: range
  - Required: true within each target
  - Type: list of issue selectors
  - Description: Selects individual issues and inclusive issue-number ranges.
  - Possible Values: An integer ≥ 1, or a two-integer list whose first value is ≥ 1 and whose second value is ≥ -1. `-1` means the latest issue.
  - Notes: Reversed ranges and ranges beyond the repository's newest issue are skipped during sanitization. Nested lists deeper than one level are invalid. Overlapping selectors, such as `[1, [1, 3], 2]`, do not produce duplicate API extraction because each issue is filtered once.
- Name: comments
  - Required: true in top-level `fields`, optional in target overrides
  - Type: list of strings
  - Description: Data points to mine from issue comments.
  - Possible Values: `body`, `created_at`, `userid`, `userlogin`, `usertype`.
  - Notes: May be an empty list if no comment data are needed. (See `repo_extractor/schema.py > cmd_tbl` for the authoritative list.)
- Name: commits
  - Required: true in top-level `fields`, optional in target overrides
  - Type: list of strings
  - Description: Data points to mine from commits associated with PRs.
  - Possible Values: `author_name`, `committer`, `date`, `files`, `message`, `sha`.
  - Notes: Gathered only for issues that are PRs. May be an empty list. (See `repo_extractor/schema.py > cmd_tbl`.)
- Name: review_comments
  - Required: false
  - Type: list of strings
  - Description: Data points to mine from inline pull-request review comments.
  - Possible Values: `body`, `commit_id`, `created_at`, `diff_hunk`, `id`, `line`, `path`, `pull_request_review_id`, `updated_at`, `userid`, `userlogin`, `usertype`.
  - Notes: Gathered only for pull requests. This includes inline comments made by Copilot Code Review under `copilot-pull-request-reviewer[bot]`.
- Name: reviews
  - Required: false
  - Type: list of strings
  - Description: Data points to mine from pull-request review records, including review summary bodies.
  - Possible Values: `body`, `commit_id`, `id`, `state`, `submitted_at`, `userid`, `userlogin`, `usertype`.
  - Notes: Gathered only for pull requests.
- Name: issues
  - Required: true in top-level `fields`, optional in target overrides
  - Type: list of strings
  - Description: Data points to mine from issue metadata.
  - Possible Values: `body`, `closed_at`, `created_at`, `num_comments`, `title`, `userid`, `userlogin`, `usertype`.
  - Notes: Gathered only for issues that are also PRs (commits are irrelevant to stand-alone issues). May be an empty list. (See `repo_extractor/schema.py > cmd_tbl`.)
