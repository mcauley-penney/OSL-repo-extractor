"""TODO:"""


import logging
import github
from base import conf, sessions, utils


class Extractor:

    """
    # TODO:
    #   1. data extraction methods
    #   2. data writing methods

    TODO: update
    The extractor class contains and executes GitHub REST API
    functionality. It holds onto a configuration object, initiates and
    holds onto the connection to GitHub, asks for information from GitHub and
    stores it in a dataset object, and has the ability to write that dataeset
    to JSON or a database.

    """

    def __init__(self, cfg_path) -> None:
        """
        TODO: Description

        :rtype None: initializes extractor object
        """
        self.__logger = logging.getLogger(__name__)

        self.__logger.info("Beginning extractor init, instantiating cfg...\n")

        # initialize tools
        self.cfg = conf.Cfg(cfg_path)
        self.gh_sesh = sessions.GithubSession(self.cfg.get_cfg_val("auth_file"))

        self.cur_pr = None

        # self.get_paged_list("issues")
        self.get_paged_list("pr")

    def __check_row_quant_safety(self, paged_list) -> int:

        row_quant = self.cfg.get_cfg_val("rows")

        if row_quant < 1 or paged_list.totalCount < row_quant:
            row_quant = paged_list.totalCount

        return row_quant

    def get_paged_list(self, list_type):
        """
        retrieve and store a paginated list from GitHub

        :param list_type str: type of paginated list to retrieve
        :rtype None: sets object member to paginated list object
        """

        job_repo = self.cfg.get_cfg_val("repo")

        try:
            # retrieve GitHub repo object
            repo_obj = self.gh_sesh.session.get_repo(job_repo)

            if list_type == "issues":
                self.__logger.info(utils.LOG_DICT["G_PAGED_ISSUES"])

                self.issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state="closed"
                )

            if list_type == "pr":
                self.__logger.info(utils.LOG_DICT["G_PAGED_PR"])

                self.pr_paged_list = repo_obj.get_pulls(
                    direction="asc", sort="created", state="closed"
                )

            self.gh_sesh.print_rem_calls()

            self.__logger.info("COMPLETE!")

        except github.RateLimitExceededException:
            print()
            self.gh_sesh.sleep(utils.LOG_DICT["G_MORE_PAGES"])

    def get_pr_info(self):
        """
        Retrieves PR data points from the selected repository. Which PR data is
        retrieved is defined in the "pr_fields" line in the configuration file

        TODO:
            - add more data to choose from
            - ability to preempt collection if merged is false?
            - get commits
            - add messaging functionality, e.g. email or text
            - IMPORTANT: add ability to save data and RETURN TO SAME POSITION
        """

        def __get_pr_data_pts(field_list):
            """
            Takes a list of desired data items as strings and, for each string, gets
            the corresponding piece of data from a dictionary that matches that string
            to the data. Aggregrates the resulting data as a list, executes any function
            calls in that list, and returns the list.

            As mentioned above, the val in the dictionary may be a function call. These
            function calls are used to either allow the desired piece of data to be
            modified before being returned, e.g. having newlines removed from a string,
            or to stop the API call to GitHub servers from being executed upon
            assignment to the dictionary. Some items, such as nested data (e.g.
            current_pr.user.login/name) require a call to get the next level/submodule
            of data (user, in this case) and that call will be executed when it is
            assigned as a val to a key in the dictionary. To preempt this, we store the
            call in a function, maybe a lambda, and execute the call after it has been
            placed in the outgoing list of data.

            :param field_list list[str]: list of strings that indicate what fields are
            desired from the current pull request

            :param cur_pr github.PullRequest.PullRequest: current pull request,
            retrieved from paginated list of pull requests
            """

            merged = cur_pr.merged
            output_list = [cur_pr.number, merged]

            # assumes that we only want data from a PR that has been merged
            if merged:
                # - assumes that the pr number and merged status will not be asked
                #   for in cfg
                # - filters out invalid key requests
                whole_list = [utils.PR_CMD_DICT[field] for field in field_list]

                # iterate through list of retrieved dict vals and, if any are
                # executable, execute them and append their output to the
                # list of data to return
                output_list += [
                    item(cur_pr) if callable(item) else item for item in whole_list
                ]

            return output_list

        self.__logger.info(utils.LOG_DICT["G_DATA_PR"])

        i = 0
        pr_data = []

        # get user-chosen PR fields to procure
        desired_field_list = self.cfg.get_cfg_val("pr_fields")

        # adjust amount of rows to get if unsafe
        safe_row_quant = self.__check_row_quant_safety(self.pr_paged_list)

        while i < safe_row_quant:
            try:
                cur_pr = self.pr_paged_list[i]
                cur_pr_data = __get_pr_data_pts(desired_field_list)
                print(cur_pr_data)

            except github.RateLimitExceededException:
                self.gh_sesh.sleep(utils.LOG_DICT["G_MORE_PR"])

            else:
                pr_data.append(cur_pr_data)
                self.gh_sesh.print_rem_calls()

                i = i + 1

        # TODO: Add messaging functionality here
