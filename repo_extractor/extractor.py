"""Exposes functionality to mine GitHub repositories."""

import socket
import sys
import time
import traceback
import github
from repo_extractor import conf, schema, utils

# ANSI escape sequence for clearing a row in the console:
# credit: https://stackoverflow.com/a/64245513
CLR = "\x1b[K"
TAB = " " * 4


class GithubSession:
    """Functionality for verified connections to the GitHub API."""

    __page_len: int
    session: github.Github

    def __init__(self, auth_path: str) -> None:
        """
        Initialize GitHub session object.

        Notes:
            paginated lists are set to return 30 items per page
                by default. See
                https://docs.github.com/en/rest/overview/resources-in-the-rest-api#pagination
                for more information.

        Args:
            auth_path (str): path to file containing personal
                access token.

        Attributes:
            __page_len (int): amount of items per page in paginated
                lists.
            session (github.Github): object containing connection to
                GitHub.
        """
        self.__page_len: int = 30
        self.session = self.__get_gh_session(auth_path)

    def __get_gh_session(self, auth_path: str) -> github.Github:
        """
        Retrieve PAT from auth file and check whether it is valid.

        Args:
            auth_path (str): path to file containing personal access token.

        Raises:
            github.BadCredentialsException: string read from file is not
                a valid Personal Access Token.

            github.RateLimitExceededException: if rate limited
                by the GitHub REST API, return the authorized session.
                If rate limited, it means that the given PAT is valid
                and a usable connection has been made.

        Returns:
            github.Github: session object or exit.
        """
        # retrieve token from auth file
        token = utils.read_file_line(auth_path)

        # establish a session with token
        session = github.Github(
            token, per_page=self.__page_len, retry=100, timeout=100
        )

        try:
            # if name can be gathered from token, properly authenticated
            session.get_user().id

        except github.BadCredentialsException:
            print("Invalid personal access token found! Exiting...\n")
            sys.exit(1)

        # if rate limited at this stage, session must be valid
        except github.RateLimitExceededException:
            return session

        return session

    def get_pg_len(self):
        """Get the page length of paginated lists for this connection."""
        return self.__page_len

    def get_remaining_calls(self) -> str:
        """Get remaining calls to REST API for this hour."""
        calls_left = self.session.rate_limiting[0]

        return f"{calls_left:<4d}"

    def get_remaining_ratelimit_time(self) -> int:
        """
        Get the remaining time before rate limit resets.

        Note: If this value is not between 1 hour and 00:00 check
              your system clock for correctness.

        Returns:
            int: amount of time until ratelimit expires.
        """
        return self.session.rate_limiting_resettime - int(time.time())


class Extractor:
    """The Extractor class contains GitHub REST API functionality."""

    # ----------------------------------------------------------------------
    # Initialization tools
    # ----------------------------------------------------------------------
    def __init__(self, cfg_obj: conf.Cfg) -> None:
        """
        Extractor object initialization.

        This object is our top-level actor and must be used by the user
        to extract data, such as in a driver program.

        Args:
            cfg_obj (conf.Cfg): configuration object.

        Attributes:
            cfg (conf.Cfg): configuration object.
            gh_sesh (github.Github): GitHub connection object.
            issues_paged_list (github.PaginatedList of github.Issue): the
                paginated list containing all issues of the chosen type
                for the repository.
        """
        self.cfg = cfg_obj

        # initialize authenticated GitHub session so that we can
        # interact with the API
        self.gh_sesh = GithubSession(self.cfg.get_cfg_val("auth_path"))

        self.paged_list = self.__get_issues_paged_list(
            self.__get_repo_obj(), self.cfg.get_cfg_val("state")
        )

        self.cfg.set_cfg_val("range", self.__get_sanitized_cfg_range())

    def __get_repo_obj(self):
        """
        TODO.

        Returns:
            github.Repository.Repository: repo obj for current extraction op
        """
        job_repo = self.cfg.get_cfg_val("repo")

        while True:
            try:
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            except github.UnknownObjectException:
                print(f'{TAB}Cannot access "{job_repo}"!')
                print(f"{TAB}It either does not exist or is private!")
                sys.exit(1)

            else:
                return repo_obj

    def __get_issues_paged_list(self, repo_obj, state: str):
        """
        Retrieve and store a paginated list from GitHub.

        Raises:
            github.RateLimitExceededException: if rate limited
                by the GitHub REST API, sleep the program until
                calls can be made again and continue attempt to
                collect desired paginated list.

            github.UnknownObjectException: this exception is
                thrown at least when a repository is not
                accessible. This is can occur because the repo
                is private or does not exist, but may occur
                for other, unforeseen reasons.

        Returns:
            github.PaginatedList of github.Issue.
        """
        while True:
            try:
                issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state=state
                )

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            else:
                return issues_paged_list

    def __get_sanitized_cfg_range(self) -> tuple:
        """
        Ensure that issue numbers to be mined exist.

        This will correct any vals given in the range configuration
        so that they are within the values that are in the paginated
        list of items. For example, if you give [10,100] in the cfg
        and the repo has 9 issues, this will round the offending values
        down. We are protected from too low of values by the config json
        schema, so this process only looks at values that are too high.

        Returns:
            tuple[int, ...]
        """
        print(f"{TAB}Sanitizing range...")

        last_page_index: int = (
            self.paged_list.totalCount - 1
        ) // self.gh_sesh.get_pg_len()

        last_page = self.paged_list.get_page(last_page_index)

        last_num: int = last_page[-1].number
        print(f"{TAB * 2}Last item number: {last_num}")

        range_list: list[int] = self.cfg.get_cfg_val("range")

        # get sanitized range:
        clean_range: tuple[int, ...] = tuple(
            min(val, last_num) for val in range_list
        )

        print(f"{TAB * 2}Range cleaned: {clean_range[0]} to {clean_range[-1]}")

        return clean_range

    # ----------------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------------
    @staticmethod
    def __get_item_data(fields: list, cmd_tbl: dict, cur_item) -> dict:
        """
        Getter engine used to aggregate desired data from a given API item.

        For each field in the list provided by the user in
        configuration, e.g. "issue_fields", get the associated
        piece of data and store it in a dict where
        {field name: field data}, e.g. {"issue number": 20}.

        Args:
            user_cfg (conf.Cfg): Cfg object containing user-provided
                configuration
            item_type (str): name of item type to retrieve, e.g.
                "pr" or "issue"
            cur_item (github.Issue/PullRequest/Commit): the current
                API item to get data about, e.g. current PR

        Returns:
            dict: dictionary of API data values for param item
        """
        # when called, this will resolve to various function calls, e.g.
        # "body": cmd_tbl["body"](cur_PR)
        return {field: cmd_tbl[field](cur_item) for field in fields}

    def __sleep_extractor(self) -> None:
        """Sleep the program until we can make calls again."""
        cntdwn_time = self.gh_sesh.get_remaining_ratelimit_time()

        while cntdwn_time > 0:

            # modulo function returns time tuple
            minutes, seconds = divmod(cntdwn_time, 60)

            # format the time string before printing
            cntdown_str = f"{minutes:02d}:{seconds:02d}"

            print(
                f"{CLR}{TAB * 2}Time until limit reset: {cntdown_str}",
                end="\r",
            )

            # sleep for a while
            time.sleep(1)
            cntdwn_time -= 1

        print(f"{CLR}{TAB * 2}Starting data collection...", end="\r")

    # ----------------------------------------------------------------------
    # Public methods
    #
    # Top-level actors are listed above their helper functions.
    # If a helper is capable of being used by more than one,
    # it will be listed above this heading.
    # ----------------------------------------------------------------------
    def get_repo_issues_data(self) -> None:
        """
        Gather all chosen data points from chosen issue numbers.

        This method is our access point into the GitHub API, the
        primary tool afforded by the Extractor class to the user.

        Raises:
            github.RateLimitExceededException: if rate limited
                by the GitHub REST API, dump collected data to
                output file and sleep the program until calls
                can be made again.
        """
        func_schema: dict = {
            "issues": self.__get_item_data,
            "commits": self.__get_issue_commits,
            "comments": self.__get_issue_comments,
        }

        out_data: dict = {}
        output_file: str = self.cfg.get_cfg_val("output_path")
        issue_range: list = self.cfg.get_cfg_val("range")

        start_index: int = self.__get_issue_index_by_num(issue_range[0])
        end_index: int = self.__get_issue_index_by_num(issue_range[-1])

        print(
            f"{TAB}Starting issue mining at #{issue_range[0]}. Please wait..."
        )

        while start_index < end_index + 1:
            cur_item_data: dict = {}
            cur_issue_data: dict = {}

            cur_issue = self.paged_list[start_index]

            try:
                for key, func in func_schema.items():
                    if self.cfg.get_cfg_val(key):
                        cur_item_data = func(
                            self.cfg.get_cfg_val(key),
                            schema.cmd_tbl[key],
                            cur_issue,
                        )

                        cur_issue_data |= cur_item_data

                cur_total_entry = {str(cur_issue.number): cur_issue_data}

            except github.RateLimitExceededException:
                utils.write_merged_dict_to_jsonfile(out_data, output_file)

                # clear dictionary so that it isn't massive and
                # holding onto data that we have already written
                # to output
                out_data.clear()
                self.__sleep_extractor()

            except (
                KeyboardInterrupt,
                github.GithubException,
                socket.error,
                socket.gaierror,
            ):

                traceback.print_exc()
                print("\n\n Writing gathered data...")
                utils.write_merged_dict_to_jsonfile(out_data, output_file)
                print(f"{TAB}Terminating at item #{cur_issue.number}\n")
                sys.exit(1)

            else:
                out_data |= cur_total_entry

                print(f"{CLR}{TAB * 2}", end="")
                print(f"Issue: {cur_issue.number}, ", end="")
                print(
                    f"calls: {self.gh_sesh.get_remaining_calls()}",
                    end="\r",
                )

                start_index += 1

        utils.write_merged_dict_to_jsonfile(out_data, output_file)

        print()

    def __get_issue_comments(self, fields: list, cmd_tbl: dict, issue) -> dict:
        """
        Create a dict of issue comment data for the given issue param.

        If the user chose to ask the API for data about issue comments,
        get a paginated list of comments from an issue, get the desired
        data from them, and return a dict of that data.

        Args:
            datatype_dict(dict): dict of fields to get for issues from cfg.
            issue_obj (Github.Issue): issue to get comment data from.

        Returns:
            dict|None: If the user does not ask for comment data,
            return None. Else, attempt to gather comment data points.
        """
        item_type = "comments"

        # dict will hold data related to all comments for an
        # issue. Issue to comments is a one to many relationship
        comment_index: int = 0
        cur_comment_data: dict = {}

        for comment in issue.get_comments():
            cur_entry = self.__get_item_data(fields, cmd_tbl, comment)

            cur_entry = {str(comment_index): cur_entry}

            cur_comment_data |= cur_entry

            comment_index += 1

        return {item_type: cur_comment_data}

    def __get_issue_commits(self, fields: list, cmd_tbl: dict, issue) -> dict:
        """TODO."""

        def get_as_pr(cur_issue):
            try:
                cur_pr = cur_issue.as_pull_request()

            except github.UnknownObjectException:
                # Not a PR, does not need to raise an error.
                # Return up and keep going
                return None

            else:
                return cur_pr

        def __get_commit_data(pr_obj):
            """
            Return the last commit from a paginated list of commits from a PR.

            Args:
                pr_obj (github.PullRequest): PR to gather data for.

            Returns:
                Github.Commit: last commit made in PR.

            """
            field_type: str = "commits"
            commit_index: int = 0
            pr_commit_data: dict = {}

            for commit in pr_obj.get_commits():
                if commit.files:
                    commit_datum = self.__get_item_data(
                        fields, cmd_tbl, commit
                    )

                else:
                    commit_datum = {}

                pr_commit_data |= {str(commit_index): commit_datum}

                commit_index += 1

            return {field_type: pr_commit_data}

        pr_data: dict
        pr_obj = get_as_pr(issue)

        if pr_obj is not None:
            pr_data = {
                "is_pr": True,
                "state": pr_obj.state,
                "is_merged": pr_obj.merged,
                "num_review_comments": pr_obj.comments,
            }

            commit_data: dict = __get_commit_data(pr_obj)
            pr_data |= commit_data

        else:
            pr_data = {"is_pr": False}

        return pr_data

    def __get_issue_index_by_num(self, val_to_find: int):
        """
        Find indices of API items in paginated list of items.

        For example, you want to find issue #150 in the paginated
        list of issues for a repo. The index of that issue is NOT
        the same as its issue number. We must look through the
        paginated list of issues and find it.

        Args:
            val_to_find (int): the number of the API item to find

        Returns:
            int: index of the desired API item
        """
        mid: int
        low: int = 0
        high: int = self.paged_list.totalCount - 1
        page_len: int = self.gh_sesh.get_pg_len()

        while low < high:
            mid = (low + high) // 2

            page, index = divmod(mid, page_len)
            cur_val = self.paged_list.get_page(page)[index].number

            if val_to_find == cur_val:
                return mid

            if val_to_find < cur_val:
                high = mid - 1

            elif val_to_find > cur_val:
                low = mid + 1

        return low
