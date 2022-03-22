"""
The sessions module contains classes that expose functionality to the Extractor that
allow it to interact with external sources that require connections
"""

import sys
import time
import github
from src import file_io


def _console_print_in_place(label_str: str, val) -> None:
    # clear line to erase any errors due to typing in the console
    print("", end="\r")

    # print output in place
    print(f"{' ' * 4}{label_str} {val}", end="\r")


class GithubSession:
    """
    The GithubSession class initializes and holds a verified connection to the GitHub
    API and exposes functionality for that connection up to the Extractor class
    """

    __page_len: int
    session: github.Github

    def __init__(self, auth_path) -> None:
        """
        initialize GitHub session object
        NOTES:
            - paginated lists are set to return 30 items per page by default.
              See https://docs.github.com/en/rest/overview/resources-in-the-rest-api#pagination
              for more information.

        :param auth_path str: path to file containing personal access token
        """
        #
        self.__page_len = 30
        self.session = self.__get_gh_session(auth_path)

    def __get_gh_session(self, auth_path) -> github.Github:
        """
        retrieves PAT from auth file, checks whether it is valid

        :raises github.BadCredentialsException: if given item is not a valid Personal
        Access Token

        :raises github.RateLimitExceededException: if rate limited by the GitHub REST
        API, return the authorized session. If rate limited, it means that the given
        PAT is valid and a usable connection has been made

        :rtype None:
        """

        # retrieve token from auth file
        token = file_io.read_txt_line(auth_path)

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
        """
        getter method that allows access to page length of pages in GitHub API
        paginated lists
        """
        return self.__page_len

    def print_rem_gh_calls(self) -> None:
        """print remaining calls to API for this hour"""

        # get remaining calls before reset
        calls_left = self.session.rate_limiting[0]

        # format as a string
        calls_left_str = f"{calls_left:<4d}"

        _console_print_in_place("Calls left until sleep:", calls_left_str)

    def sleep_gh_session(self) -> None:
        """sleep the program until we can make calls again"""

        # time to wait is the amount of seconds until reset minus the current time
        countdown_time = self.session.rate_limiting_resettime - int(time.time())

        while countdown_time > 0:

            # modulo function returns time tuple
            minutes, seconds = divmod(countdown_time, 60)

            # format the time string before printing
            countdown_str = f"{minutes:02d}:{seconds:02d}"

            _console_print_in_place("time until limit reset:", countdown_str)

            # sleep for a while
            time.sleep(1)
            countdown_time -= 1