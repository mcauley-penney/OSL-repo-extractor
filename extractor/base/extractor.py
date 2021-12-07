""""""
# import time
# import github

# from base.utils import LOG_DICT

import logging
import time
import github
from base import auth, conf, utils


class Extractor:
    """
    # TODO:
    #   1. data extraction methods
    #   2. data writing methods


    The extractor class contains and executes GitHub REST API
    functionality. It holds onto a configuration object, initiates and
    holds onto the connection to GitHub, asks for information from GitHub and
    stores it in a dataset object, and has the ability to write that dataeset
    to JSON or a database.

    """

    def __init__(self, cfg_path) -> None:
        """
        TODO: Description

        TODO:
            - determine how we want to hold onto data
                - see "dataset member"
            - need a means of holding current session and cycling them
                - use a method to get next session and cycle


        :rtype None: initializes extractor object
        """
        self.logger = logging.getLogger(__name__)

        self.logger.info("Beginning extractor init, instantiating cfg...\n")

        # initialize configuration object
        self.cfg = conf.Cfg(cfg_path)

        auth_path = self.cfg.get_cfg_val("auth_file")

        # initialize auths object
        self.auth_obj = auth.Auth(auth_path)

        # self.dataset = None
        # self.issues_paged_list = None
        # self.pr_paged_list = None

        # Extraction functionality

    def get_paged_list(self, list_type) -> None:
        """
        retrieve and store a paginated list from GitHub

        :param list_type str: type of paginated list to retrieve
        :rtype None: sets object member to paginated list object
        """
        pages_received = False
        session_index = 0

        try:
            # retrieve GitHub repo object
            repo_obj = self.session_list[session_index].get_repo(self.cfg.repo)

            if list_type == "issues":
                self.logger.info(utils.LOG_DICT["G_PAGED_ISSUES"])

                self.issues_paged_list = repo_obj.get_issues(
                    direction="asc", sort="created", state="closed"
                )

            if list_type == "pr":
                self.logger.info(utils.LOG_DICT["G_PAGED_PR"])

                self.pr_paged_list = repo_obj.get_pulls(
                    direction="asc", sort="created", state="closed"
                )

            self.__print_rem_calls()

            self.logger.info("COMPLETE!")

        except github.RateLimitExceededException:
            print()
            self.__sleep(utils.LOG_DICT["G_MORE_PAGES"])

        # # Display functionality
        # def export_conf(self) -> None:
        #     """
        #     print the configuration provided in conf CLI arg

        #     :rtype None: logs configuration
        #     """
        #     log_str = "\nProvided configuration:\n"

        #     for key, val in self.cfg.full_cfg_text.items():
        #         log_str += f"\t{key}: {val}\n"

        #     self.logger.log_obj.info(log_str)

        # # GitHub connection management functionality
