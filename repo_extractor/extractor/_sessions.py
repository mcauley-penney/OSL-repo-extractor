"""The _sessions module contains the GithubSession class."""

import sys
import time
import github
from repo_extractor.utils import file_io_utils


class GithubSession:
    """Initialize and expose functionality for verified connections to the GitHub API."""

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
        token = file_io_utils.read_file_line(auth_path)

        # establish a session with token
        session = github.Github(token, per_page=self.__page_len, retry=100, timeout=100)

        try:
            # if name can be gathered from token, properly authenticated
            session.get_user().name

        # if token is not valid, remove token from list
        except github.BadCredentialsException:
            # log that token is invalid
            print("Invalid personal access token found! Exiting...\n")
            sys.exit(1)

        # if rate limited at this stage, session must be valid
        except github.RateLimitExceededException:
            return session

        else:
            return session

    def get_pg_len(self):
        """Get the page length setting of paginated lists for this Github connection."""
        return self.__page_len

    def get_remaining_calls(self) -> str:
        """Get remaining calls to REST API for this hour."""
        # get remaining calls before reset
        calls_left = self.session.rate_limiting[0]

        # format as a string
        return f"{calls_left:<4d}"

    def get_remaining_ratelimit_time(self) -> int:
        """Get the remaining time before rate limit resets."""
        # time to wait is the amount of seconds until reset minus
        # the current time. If this value is incorrect or extreme
        # check your system clock for correctness. It should always
        # be between 1 hour and 00:00
        return self.session.rate_limiting_resettime - int(time.time())
