"""Exposes functionality to mine GitHub repositories."""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
import socket
import time

import github

from repo_extractor import schema, utils

# ANSI escape sequence for clearing a row in the console:
# credit: https://stackoverflow.com/a/64245513
CLR = "\x1b[K"
TAB = " " * 4

FlushCallback = Callable[[str, dict], None]
ItemResultCallback = Callable[[str, int, bool, bool, dict | None], None]


class GithubSessionError(RuntimeError):
    """Raised when a GitHub session cannot be established safely."""


class ExtractorError(RuntimeError):
    """Raised when repository extraction cannot complete successfully."""


class ItemExtractionError(RuntimeError):
    """Wrap an expected item failure with the extraction operation involved."""

    def __init__(self, operation: str, cause: Exception) -> None:
        super().__init__(str(cause))
        self.operation = operation
        self.cause = cause


class GithubSession:
    """Functionality for verified connections to the GitHub API."""

    __page_len: int
    session: github.Github

    def __init__(self, auth_path: str) -> None:
        """
        Initialize GitHub session object.

        Notes:
            Paginated lists are set to return 100 items per page. See
            https://docs.github.com/en/rest/overview/resources-in-the-rest-api#pagination
            for more information.

        Args:
            auth_path (str): path to file containing personal access token.
        """
        self.__page_len = 100
        self.session = self.__get_gh_session(auth_path)

    def __get_gh_session(self, auth_path: str) -> github.Github:
        """
        Retrieve PAT from auth file and check whether it is valid.

        Args:
            auth_path (str): path to file containing personal access token.

        Raises:
            GithubSessionError: string read from file is not a valid
                Personal Access Token.

        Returns:
            github.Github: authenticated session object.
        """
        token = utils.read_file_line(auth_path)
        session = github.Github(token, per_page=self.__page_len, retry=100, timeout=100)

        try:
            session.get_user().id
        except github.BadCredentialsException as exc:
            raise GithubSessionError("Invalid personal access token found.") from exc
        except github.RateLimitExceededException:
            return session

        return session

    def get_pg_len(self) -> int:
        """Get the configured page length."""
        return self.__page_len

    def get_remaining_calls(self) -> str:
        """Get remaining calls to REST API for this hour."""
        calls_left = self.session.rate_limiting[0]

        return f"{calls_left:<4d}"

    def get_remaining_ratelimit_time(self) -> int:
        """
        Get the remaining time before rate limit resets.

        Note: If this value is not between 1 hour and 00:00 check your
        system clock for correctness.

        Returns:
            int: amount of time until ratelimit expires.
        """
        return self.session.rate_limiting_resettime - int(time.time())


class Extractor:
    """Extract data for one normalized repository target configuration."""

    def __init__(
        self,
        target_cfg: dict,
        gh_sesh: GithubSession | None = None,
        flush_callback: FlushCallback | None = None,
        item_result_callback: ItemResultCallback | None = None,
    ) -> None:
        """
        Initialize an extractor for one repository target.

        Args:
            target_cfg (dict): normalized per-target runtime configuration.
            gh_sesh (GithubSession | None): shared GitHub session to reuse.
            flush_callback (FlushCallback | None): callback used to persist
                repo-local output chunks when partial progress should be flushed.
            item_result_callback (ItemResultCallback | None): callback used to
                record successful and skipped item results.
        """
        self.cfg = deepcopy(target_cfg)
        self.flush_callback = flush_callback
        self.item_result_callback = item_result_callback
        self.repo_slug = self.cfg["repo"]

        # Reuse a shared authenticated session when supplied by the caller.
        self.gh_sesh = gh_sesh or GithubSession(self.cfg["auth_path"])

        repo = self.__get_repo_obj()
        self.paged_list = self.__get_issues_paged_list(
            repo,
            self.cfg["state"],
            self.cfg["labels"],
        )
        self.page_cache: dict[int, list] = {}

        clean_ranges = self.__get_sanitized_cfg_ranges(repo)
        self.cfg["range"] = clean_ranges

        try:
            self.last_page_index = self.__get_last_page_index(self.paged_list)
            self.issue_manifest = self.__generate_issue_manifest(
                self.paged_list, clean_ranges
            )
        except github.GithubException as exc:
            raise ExtractorError(
                f'Cannot retrieve issues for repository "{self.repo_slug}".'
            ) from exc
        except (socket.error, socket.gaierror) as exc:
            raise ExtractorError(
                f'Cannot retrieve issues for repository "{self.repo_slug}".'
            ) from exc

    def extract_repo_data(self) -> dict:
        """
        Gather all configured data points for the current repository target.

        Returns:
            dict: repo-local extraction data keyed by issue or PR number.

        Item-level GitHub and socket errors are logged and skipped after
        pending output is flushed. They do not stop extraction of later items.

        Raises:
            KeyboardInterrupt: re-raised after pending output is flushed.
        """
        repo_data: dict = {}
        pending_output: dict = {}
        issue_ranges = self.cfg["range"]

        print(
            f"{TAB}Starting mining for {self.repo_slug} "
            f"for ranges {issue_ranges}..."
        )

        for cur_issue in self.issue_manifest:
            while True:
                try:
                    cur_issue_data = self.__collect_issue_data(cur_issue)
                except github.RateLimitExceededException:
                    self.__flush_pending_output(pending_output)
                    pending_output.clear()
                    print()
                    self.__sleep_extractor()
                    continue
                except KeyboardInterrupt:
                    self.__flush_pending_output(pending_output)
                    raise
                except ItemExtractionError as exc:
                    operation = exc.operation
                    cause = exc.cause
                except (
                    github.GithubException,
                    socket.error,
                    socket.gaierror,
                ) as exc:
                    operation = "unknown"
                    cause = exc
                else:
                    issue_number = str(cur_issue.number)
                    repo_data[issue_number] = cur_issue_data
                    pending_output[issue_number] = cur_issue_data
                    if self.item_result_callback is not None:
                        self.item_result_callback(
                            self.repo_slug,
                            cur_issue.number,
                            True,
                            getattr(cur_issue, "pull_request", None) is not None,
                            None,
                        )

                    print(
                        f"{CLR}{TAB * 2}Repo: {self.repo_slug}, "
                        f"Issue: {cur_issue.number}, ",
                        end="",
                    )
                    print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")
                    break

                self.__flush_pending_output(pending_output)
                pending_output.clear()
                error = self.__build_item_error(operation, cause)
                is_pr = getattr(cur_issue, "pull_request", None) is not None
                status = (
                    f" (GitHub status {error['status']})" if "status" in error else ""
                )
                print(
                    f"\n{TAB}Skipping unavailable item "
                    f"#{cur_issue.number} in {self.repo_slug}{status}: "
                    f"{error['message']}"
                )
                if self.item_result_callback is not None:
                    self.item_result_callback(
                        self.repo_slug,
                        cur_issue.number,
                        False,
                        is_pr,
                        error,
                    )
                break

        self.__flush_pending_output(pending_output)
        print()

        return repo_data

    def get_repo_slug(self) -> str:
        """Return the canonical repo slug for this extraction target."""
        return self.repo_slug

    def get_target_cfg(self) -> dict:
        """Return a copy of the normalized target configuration."""
        return deepcopy(self.cfg)

    def __get_repo_obj(self):
        """
        Gather the repository requested by the target configuration.

        Returns:
            github.Repository.Repository: repo object for current extraction op.

        Raises:
            ExtractorError: repository does not exist or is inaccessible.
        """
        while True:
            try:
                repo_obj = self.gh_sesh.session.get_repo(self.repo_slug)
            except github.RateLimitExceededException:
                self.__sleep_extractor()
            except github.GithubException as exc:
                raise ExtractorError(
                    f'Cannot access "{self.repo_slug}". It either does not exist '
                    f"or is private (GitHub status {exc.status})."
                ) from exc
            except (socket.error, socket.gaierror) as exc:
                raise ExtractorError(
                    f'Cannot access "{self.repo_slug}" because the GitHub '
                    "connection failed."
                ) from exc
            else:
                return repo_obj

    def __get_issues_paged_list(self, repo_obj, state: str, labels: list[str]):
        """
        Retrieve and store a paginated list from GitHub.

        Returns:
            github.PaginatedList of github.Issue.
        """
        while True:
            try:
                query = {
                    "direction": "asc",
                    "sort": "created",
                    "state": state,
                }
                if labels:
                    query["labels"] = labels

                issues_paged_list = repo_obj.get_issues(**query)
            except github.RateLimitExceededException:
                self.__sleep_extractor()
            except github.GithubException as exc:
                raise ExtractorError(
                    f'Cannot retrieve issues for repository "{self.repo_slug}" '
                    f"(GitHub status {exc.status})."
                ) from exc
            except (socket.error, socket.gaierror) as exc:
                raise ExtractorError(
                    f'Cannot retrieve issues for repository "{self.repo_slug}" '
                    "because the GitHub connection failed."
                ) from exc
            else:
                return issues_paged_list

    def __get_sanitized_cfg_ranges(self, repo) -> list[int]:
        """
        Ensure that target issue selectors are available in the repository.

        Reversed ranges and selectors beyond the newest repository item are
        skipped. Overlapping selectors are harmless because each API item is
        considered once while filtering the paginated list.

        Returns:
            list[tuple[int, int]]: cleaned inclusive ranges.
        """
        print(f"{TAB}Sanitizing range for {self.repo_slug}...")

        last_item_num = self.__get_last_item_num(repo)

        print(f"{TAB * 2}Last item: #{last_item_num}")

        clean_ranges: list[int] = []

        for selector in self.cfg["range"]:
            if isinstance(selector, int):
                start = end = selector
            else:
                start, end = selector
                end = last_item_num if end == -1 else end

            end = min(end, last_item_num)
            if start > last_item_num or start > end:
                print(f"{TAB * 2}Skipping invalid selector: {selector}")
                continue

            clean_ranges.extend(range(start, end + 1))

        print(f"{TAB * 2}Cleaned ranges: {clean_ranges}")
        return clean_ranges

    def __get_last_item_num(self, repo) -> int:
        """Return the newest issue or PR number in the repository."""
        while True:
            try:
                issues_desc = repo.get_issues(
                    direction="desc",
                    sort="created",
                    state="all",
                )
                newest_issue = next(iter(issues_desc), None)
            except github.RateLimitExceededException:
                self.__sleep_extractor()
            except github.GithubException as exc:
                raise ExtractorError(
                    f"Cannot determine the latest issue for repository "
                    f'"{self.repo_slug}" (GitHub status {exc.status}).'
                ) from exc
            except (socket.error, socket.gaierror) as exc:
                raise ExtractorError(
                    f"Cannot determine the latest issue for repository "
                    f'"{self.repo_slug}" because the GitHub connection failed.'
                ) from exc
            else:
                return newest_issue.number if newest_issue is not None else 0

    @staticmethod
    def __get_item_data(fields: list, cmd_tbl: dict, cur_item) -> dict:
        """
        Aggregate selected data fields from a given API item.

        Args:
            fields (list): configured field names to retrieve.
            cmd_tbl (dict): dispatch table for the current item type.
            cur_item (github API object): current API item to inspect.

        Returns:
            dict: dictionary of API data values for the given item.
        """
        return {field: cmd_tbl[field](cur_item) for field in fields}

    def __collect_issue_data(self, issue) -> dict:
        """Collect all configured data for a single issue or PR."""
        func_schema = (
            ("issues", self.__get_item_data),
            ("commits", self.__get_issue_commits),
            ("comments", self.__get_issue_comments),
        )

        cur_issue_data: dict = {}

        for key, func in func_schema:
            fields = self.cfg[key]

            if fields:
                try:
                    cur_issue_data |= func(
                        fields,
                        schema.cmd_tbl[key],
                        issue,
                    )
                except github.RateLimitExceededException:
                    raise
                except (
                    github.GithubException,
                    socket.error,
                    socket.gaierror,
                ) as exc:
                    raise ItemExtractionError(key, exc) from exc

        return cur_issue_data

    def __flush_pending_output(self, repo_data_chunk: dict) -> None:
        """
        Flush pending repo-local output through the configured callback.

        Args:
            repo_data_chunk (dict): issue-number keyed data chunk to flush.
        """
        if not repo_data_chunk or self.flush_callback is None:
            return

        self.flush_callback(self.repo_slug, deepcopy(repo_data_chunk))

    def __sleep_extractor(self) -> None:
        """
        Sleep until the rate limit on the GitHub account expires.

        Notes:
            If the system clock is inaccurate, this method cannot give an
            accurate amount of time until limit reset.
        """
        print()

        rate_limit = self.gh_sesh.get_remaining_ratelimit_time()
        while rate_limit > 0:
            minutes, seconds = divmod(rate_limit, 60)
            cntdown_str = f"{minutes:02d}:{seconds:02d}"

            print(
                f"{CLR}{TAB}Time until limit reset: {cntdown_str}",
                end="\r",
            )

            time.sleep(1)
            rate_limit -= 1

        while True:
            try:
                self.gh_sesh.session.get_user().id
            except github.RateLimitExceededException:
                print(
                    f"{CLR}{TAB}Waiting for rate limit to lift...",
                    end="\r",
                )
                time.sleep(10)
            else:
                cur_time = time.strftime("%I:%M:%S %p", time.localtime())
                print(f"{CLR}{TAB}Rate limit lifted! The time is {cur_time}...")
                return None

    @staticmethod
    def __build_item_error(operation: str, cause: Exception) -> dict:
        """Build JSON-safe error metadata for a failed item operation."""
        error = {
            "operation": operation,
            "message": str(cause),
        }
        if isinstance(cause, github.GithubException):
            error["status"] = cause.status
        return error

    def __get_page(self, paged_list, page_index: int) -> list:
        """Return a page, reusing it when a search already fetched it."""
        if page_index not in self.page_cache:
            self.page_cache[page_index] = paged_list.get_page(page_index)
        return self.page_cache[page_index]

    def __get_last_page_index(self, paged_list) -> int:
        """Find the final non-empty page in the paged list.

        GitHub's issues endpoint now returns cursor-based ``next`` links without
        a ``last`` link. PyGithub consequently reports the size of its one-item
        count probe as ``totalCount``. Indexed page requests still work, so an
        exponential search followed by a binary search establishes the usable
        page boundary in logarithmic requests.
        """

        print(f"{TAB}Surveying available issues for {self.repo_slug}...")

        if not self.__get_page(paged_list, 0):
            return -1

        last_nonempty = 0
        first_empty = 1

        while self.__get_page(paged_list, first_empty):
            last_nonempty = first_empty
            first_empty *= 2

        low = last_nonempty + 1
        high = first_empty - 1

        while low <= high:
            mid = (low + high) // 2
            if self.__get_page(paged_list, mid):
                last_nonempty = mid
                low = mid + 1
            else:
                high = mid - 1

        return last_nonempty

    def __generate_issue_manifest(self, paged_list, issue_extraction_range) -> list:
        """Return exactly matching issues from the configured selection."""
        issue_manifest = []

        for issue_num in issue_extraction_range:
            issue = self.__find_issue_in_paged_list(paged_list, issue_num)
            if issue is None:
                print(
                    f"{TAB * 2}Item #{issue_num} does not match the configured "
                    "state and labels; skipping."
                )
                continue
            issue_manifest.append(issue)

        return issue_manifest

    def __get_issue_comments(self, fields: list, cmd_tbl: dict, issue) -> dict:
        """
        Get issue comment data for the given issue.

        Args:
            issue (github.issue): issue to gather data about.
            fields (list): list of comment fields to gather from the issue.
            cmd_tbl (dict): dict of {field: function to get field}.

        Returns:
            dict: dictionary of {comment index: comment data}.
        """
        comment_index = 0
        cur_comment_data: dict = {}

        for comment in issue.get_comments():
            cur_entry = self.__get_item_data(fields, cmd_tbl, comment)
            cur_comment_data[str(comment_index)] = cur_entry
            comment_index += 1

        return {"comments": cur_comment_data}

    def __get_issue_commits(self, fields: list, cmd_tbl: dict, issue) -> dict:
        """
        Get issue commit data for the given issue.

        Args:
            issue (github.issue): issue to gather data about.
            fields (list): list of commit fields to gather from the issue.
            cmd_tbl (dict): dict of {field: function to get field}.

        Returns:
            dict: PR metadata and, if applicable, {commit index: commit data}.
        """

        def as_pr(cur_issue):
            try:
                cur_pr = cur_issue.as_pull_request()

            except github.UnknownObjectException:
                # A normal issue returns 404 when probed as a PR. If the
                # issues endpoint identified it as a PR, however, the PR has
                # disappeared or is inaccessible and the item should be
                # skipped by the caller.
                if getattr(cur_issue, "pull_request", None) is not None:
                    raise
                return None
            else:
                return cur_pr

        def get_commit_data(pr_obj):
            """Return commit data from a paginated list of commits from a PR."""
            commit_index = 0
            pr_commit_data: dict = {}

            for commit in pr_obj.get_commits():
                if commit.files:
                    commit_datum = self.__get_item_data(fields, cmd_tbl, commit)
                else:
                    commit_datum = {}

                pr_commit_data[str(commit_index)] = commit_datum
                commit_index += 1

            return {"commits": pr_commit_data}

        pr_obj = as_pr(issue)

        if pr_obj is not None:
            pr_data = {
                "is_pr": True,
                "state": pr_obj.state,
                "is_merged": pr_obj.merged,
                "num_review_comments": pr_obj.comments,
            }
            pr_data |= get_commit_data(pr_obj)

            return pr_data

        return {"is_pr": False}

    def __find_issue_in_paged_list(self, paged_list, issue_num: int):
        """Find an exact issue-number match in a paginated issue list.

        Args:
            paged_list (Github.PaginatedList of Github.Issue): paginated
                list of issues
            issue_num (int): the number of the desired issue

        Returns:
            github.Issue | None: matching API item, or ``None`` when the item
                is excluded by the configured state or labels.
        """
        print(f"{TAB}Finding index of item #{issue_num}...")

        low = 0
        high = self.last_page_index

        while low <= high:
            page_index = (low + high) // 2
            page = self.__get_page(paged_list, page_index)

            if issue_num < page[0].number:
                high = page_index - 1
                continue
            if issue_num > page[-1].number:
                low = page_index + 1
                continue

            numbers = [item.number for item in page]
            item_index = bisect_left(numbers, issue_num)
            if item_index < len(page) and numbers[item_index] == issue_num:
                print(f"{TAB * 2}Found on page {page_index} at index " f"{item_index}!")
                return page[item_index]
            return None

        return None
