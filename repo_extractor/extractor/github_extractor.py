"""The github_extractor module provides and exposes functionality to mine GitHub repositories."""

import datetime
import sys
import time
import github
from repo_extractor import conf, schema
from repo_extractor.extractor import _sessions
from repo_extractor.utils import dict_utils, file_io_utils


# ANSI escape sequence for clearing a row in the console:
# credit: https://stackoverflow.com/a/64245513
CLR = "\x1b[K"
TAB = " " * 4


class Extractor:
    """The Extractor class contains and executes GitHub REST API functionality."""

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

        auth_path = self.get_cfg_val("auth_file")

        # initialize authenticated GitHub session
        self.gh_sesh = _sessions.GithubSession(auth_path)

        self.repo_obj = self.__get_repo_obj()

    def __get_repo_obj(self):
        """
        TODO.

        Returns:
            github.Repository.Repository: repo obj for current extraction op
        """
        job_repo = self.get_cfg_val("repo")

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            except github.UnknownObjectException:
                print(f'{TAB}Repo "{job_repo}" either does not exist or is private!')
                sys.exit(1)

            else:
                return repo_obj

        # get index of last page in paginated list
        last_page_index = (paged_list.totalCount - 1) // page_len

        print(f"{TAB}Sanitizing range configuration values...")

        clean_range_list = __get_sanitized_range_vals(
            issue_opts_dict["range"], last_page_index
        )

        print(f"{TAB}finding start and end indices corresponding to range values...")

        # for the two boundaries in the sanitized range
        for val in clean_range_list:
            val_index = __get_issue_num_paginated_index(val, last_page_index, page_len)
            out_list.append(val_index)

            print(
                f"{TAB * 2}item #{val} found at index {val_index} in the paginated list..."
            )

        print()

        return out_list

    def get_cfg_val(self, key: str):
        """
        Wrap cfg.get_cfg_val for brevity.

        Args:
            key (str): key of desired value from configuration dict to get.

        Returns:
            value from configuration dict.

        Todo:
            give the output a comprehensive type and adjust other
            methods accordingly.
        """
        return self.cfg.get_cfg_val(key)

    def __get_commit_datum(self, commit_opts: dict, cur_commit):
        """
        Retrieve data for a single commit and return it in a dictionary.

        Wrapper around API getter engine.

        Args:
            cur_commit (github.Commit): commit to gather data for.

        Returns:
            dict: dictionary containing data from commit parameter.

            key = commit SHA
            val = commit data
        """
        cur_commit_data = self.__get_item_data(commit_opts, "commit", cur_commit)

        return {cur_commit.sha: cur_commit_data}

    @staticmethod
    def __get_item_data(category_dict: dict, field_type: str, cur_item) -> dict:
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
        field_list = category_dict[f"{field_type}_fields"]

        if len(field_list) > 0:
            cmd_tbl = schema.cmd_tbl_dict[field_type]

            # when called, this will resolve to various function calls, e.g.
            # "body": cmd_tbl["body"](cur_PR)
            return {field: cmd_tbl[field](cur_item) for field in field_list}

        return {}

    def get_repo_commit_data(self) -> None:
        """
        Create a dict of contributors and their contributions.

        The project is interested in determining the core contributors for
        a given repository. To do this, we have implemented the algorithm
        discussed in Coelho et al., 2018 (see citation below) wherein the
        contributors whose sum commits are 80% of the total commits for the
        repo are aggregated and those who have less than five commits are
        disregarded. This implementation is found in the OSL metrics
        aggregator. This method creates a dict of all contributors,
        descendingly ordered by total commits, for input into the Coelho
        et al. custom "Commit-Based Heuristic" algorithm.

        Citations:
            Coelho J, Valente MT, Silva LL, Hora A (2018) Why we engage in
            floss: Answers from core developers. In: Proceedings of the 11th
            International Workshop on Cooperative and Human Aspects of
            Software Engineering, pp 114–121

            link: https://arxiv.org/pdf/1803.05741.pdf
        """

        def __get_dev_contributions(commits, num_commits):
            """
            TODO.

            Args:
                num_commits ():

            Returns:
                dict: sorted dictionary of (contributor: contributions) pairs
            """
            contrib_dict = {}
            i = 0
            print(f"{TAB * 2}total: {total_commits}")

            while i < num_commits:
                try:
                    author = commits[i].commit.author.name

                    if author not in contrib_dict:
                        contrib_dict[author] = 1

                    else:
                        contrib_dict[author] += 1

                except github.RateLimitExceededException:
                    self.__update_output_json_for_sleep(data_dict, out_file)

                else:
                    print(f"{CLR}{TAB * 2}", end="")
                    print(f"index: {i}, ", end="")
                    print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")
                    i += 1

            return dict(sorted(contrib_dict.items(), key=lambda x: x[1], reverse=True))

        data_dict: dict = {}

        commits_opts: dict = self.cfg.cfg_dict["repo_data"]["by_commit"]
        timeframe_dict: dict = commits_opts["timeframe"]
        commits_list = self.__get_commits_paged_list(commits_opts)

        out_file: str = self.get_cfg_val("issue_output_file")
        total_commits: int = commits_list.totalCount

        data_dict["num_commits"] = total_commits

        data_dict["contributions"] = __get_dev_contributions(
            commits_list, total_commits
        )

        # nest commit data in appropriate label
        data_dict = {
            "by_commit": {timeframe_dict["since"]: {timeframe_dict["until"]: data_dict}}
        }

        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

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
        issue_opts: dict = self.cfg.cfg_dict["repo_data"]["by_issue"]

        paged_list = self.__get_issues_paged_list(issue_opts)

        data_dict = {}
        out_file = self.get_cfg_val("issue_output_file")

        # get indices of sanitized range values
        range_list: list[int] = self.__get_range_api_indices(paged_list, issue_opts)

        start_val = range_list[0]

        print(f"{TAB}Beginning issue extraction. This may take a moment...\n")

        while start_val < range_list[1] + 1:
            try:
                cur_issue = paged_list[start_val]

                # get issue data
                cur_issue_dict = self.__get_item_data(issue_opts, "issue", cur_issue)

                # get issue as a PR, if it exists, and get its data
                cur_issue_pr_dict = self.__get_issue_pr(issue_opts, cur_issue)

                # retrieve issue comments
                cur_issue_comments_dict = self.__get_issue_comments(
                    issue_opts, cur_issue
                )

                # merge the PR and issue comment dicts with the issue dict
                for entry in (cur_issue_pr_dict, cur_issue_comments_dict):
                    cur_issue_dict = dict_utils.merge_dicts(cur_issue_dict, entry)

                cur_total_entry = {str(cur_issue.number): cur_issue_dict}

            except github.RateLimitExceededException:
                self.__update_output_json_for_sleep(data_dict, out_file)

            else:
                data_dict = dict_utils.merge_dicts(data_dict, cur_total_entry)

                print(f"{CLR}{TAB * 2}", end="")
                print(f"Issue: {cur_issue.number}, ", end="")
                print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")

                start_val += 1

        data_dict = {"by_issue": data_dict}
        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

    def __get_issue_comments(self, datatype_dict: dict, issue_obj):
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
        comment_index = 0
        cur_comment_dict = {}

        for comment in issue_obj.get_comments():
            cur_entry = self.__get_item_data(datatype_dict, item_type, comment)

            cur_entry = {str(comment_index): cur_entry}

            cur_comment_dict = dict_utils.merge_dicts(cur_comment_dict, cur_entry)

            comment_index += 1

        return {item_type: cur_comment_dict}

    def __get_commits_paged_list(self, commits_opts_dict: dict):
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
        job_repo = self.get_cfg_val("repo")
        timeframe_dict: dict = commits_opts_dict["timeframe"]

        try:
            datetime_list = [
                datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                for _, date in timeframe_dict.items()
            ]

        except ValueError as err:
            print(
                f"""{TAB}ERROR: {err}
{TAB * 2}ensure that your datetime strings are of the format
{TAB * 3}'YYYY-MM-DDTHH:MM:SSZ', where 'T' and 'Z' are literal, e.g.
{TAB * 3}'1993-01-06T00:00:00Z'""",
                file=sys.stderr,
            )

            sys.exit(1)

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

                commits_paged_list = repo_obj.get_commits(
                    since=datetime_list[0], until=datetime_list[1]
                )

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            except github.UnknownObjectException:
                print(f'{TAB}Repo "{job_repo}" either does not exist or is private!')
                sys.exit(1)

            else:
                return commits_paged_list

    def __get_issues_paged_list(self, issues_opts_dict: dict):
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
        job_repo = self.get_cfg_val("repo")

        item_state = issues_opts_dict["state"]

        while True:
            try:
                # retrieve GitHub repo object
                repo_obj = self.gh_sesh.session.get_repo(job_repo)

                issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state=item_state
                )

            except github.RateLimitExceededException:
                self.__sleep_extractor()

            except github.UnknownObjectException:
                print(f'{TAB}Repo "{job_repo}" either does not exist or is private!')
                sys.exit(1)

            else:
                return issues_paged_list

    def __get_issue_pr(self, issue_opts: dict, issue_obj):
        """
        Check if an issue is a PR and, if so, collect it's PR data.

        Args:
            issue_obj (GitHub.Issue): issue to check for PR data.

        Raises:
            github.UnknownObjectException: if the given issue is not
                also a PR, the as_pull_request() method will fail and
                raise this error. In that case, we needn't do anything.

        Returns:
            dict|None: if the issue is also a PR, return a dict of
            PR info. Else, return None.
        """
        try:
            cur_pr = issue_obj.as_pull_request()

        except github.UnknownObjectException:
            # Not a PR, does not need to raise an error.
            # return up and keep going
            return None

        else:
            # return dict of PR data
            return self.__get_pr_datum(cur_pr, issue_opts)

    def __get_pr_datum(self, cur_pr, issue_opts: dict) -> dict:
        """
        Retrieve data for a single PR and return it in a dictionary.

        Args:
            cur_pr (github.PullRequest): PR to gather data for.

        Returns:
            dict: dictionary containing data from PR parameter.
        """

        def __get_last_commit(datatype_dict, pr_obj):
            """
            Return the last commit from a paginated list of commits from a PR.

            Args:
                pr_obj (github.PullRequest): PR to gather data for.

            Returns:
                Github.Commit: last commit made in PR.

            """
            last_commit_data = {}
            data_type = "commit"

            # get paginated list of commits for PR at current index
            commit_list = pr_obj.get_commits()

            last_commit = commit_list[commit_list.totalCount - 1]

            if len(last_commit.files) > 0:

                # get all data from that commit
                last_commit_data = self.__get_item_data(
                    datatype_dict, data_type, last_commit
                )

            return {data_type: last_commit_data}

        item_type = "pr"
        is_merged = cur_pr.merged
        is_valid_pr = is_merged or issue_opts["state"] == "open"

        # create dict to build upon. This variable will later become
        # the val of a dict entry, making it a subdictionary
        cur_pr_dict = {"pr_merged": is_merged}

        if is_valid_pr:
            cur_pr_data = {}
            last_commit_data = {}

            # if the current PR is merged or is in the list of open PRs, we are
            # interested in it. Closed and unmerged PRs are of no help to the
            # project
            cur_pr_data = self.__get_item_data(issue_opts, item_type, cur_pr)

            last_commit_data = __get_last_commit(issue_opts, cur_pr)

            for data_dict in (cur_pr_data, last_commit_data):
                cur_pr_dict = dict_utils.merge_dicts(cur_pr_dict, data_dict)

        # use all gathered entry data as the val for the PR num key
        return {item_type: cur_pr_dict}

    def __set_output_file_dict_val(self):
        """Create and set output directory and file paths."""
        out_dir = self.get_cfg_val("output_dir")

        # lop repo str off of full repo info, e.g. owner/repo
        repo_title = self.get_cfg_val("repo").rsplit("/", 1)[1]

        out_path = file_io_utils.mk_json_outpath(out_dir, repo_title, "issues")

        self.cfg.set_cfg_val("issue_output_file", out_path)

    def __sleep_extractor(self) -> None:
        """Sleep the program until we can make calls again."""
        cntdown_time = self.gh_sesh.get_remaining_ratelimit_time()

        while cntdown_time > 0:

            # modulo function returns time tuple
            minutes, seconds = divmod(cntdown_time, 60)

            # format the time string before printing
            cntdown_str = f"{minutes:02d}:{seconds:02d}"

            print(f"{CLR}{TAB * 2}Time until limit reset: {cntdown_str}", end="\r")

            # sleep for a while
            time.sleep(1)
            cntdown_time -= 1

        print(f"{CLR}{TAB * 2}Starting data collection...", end="\r")

    def __update_output_json_for_sleep(self, data_dict: dict, out_file: str) -> dict:
        """
        Write collected data to output and sleep the program.

        When rate limited, we can update the JSON dict in the output
        file with the data that we have collected since we were last
        rate limited.

        Args:
            data_dict (dict): dictionary of current data to write to
                output file.
            out_file (str): path to output file.

        Returns:
            dict: param dictionary, emptied.

        """
        file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

        # clear dictionary so that it isn't massive in size and storing
        # data that we have already written to output
        data_dict.clear()
        self.__sleep_extractor()

        return data_dict
