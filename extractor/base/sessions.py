"""
The Sessions module contains classes that expose functionality to the Extractor that
allow it to interact with external sources that require connections
"""

import logging
import sys
import time
import github


class GithubSession:
    """
    The GithubSession class initializes and holds a verified connection to the GitHub
    API and exposes functionality for that connection up to the Extractor class
    """

    def __init__(self, auth_path):
        """
        initialize GitHub session object

        :param auth_path str: path to file containing personal access token
        """

        self.__logger = logging.getLogger(__name__)

        self.session = self.__verify_auth(auth_path)

    def __verify_auth(self, auth_path) -> github.Github:
        """
        retrieves PAT from auth file and checks whether it is valid
        :raises github.BadCredentialsException: if given item is not a valid Personal
        Access Token

        :raises github.RateLimitExceededException: if rate limited by the GitHub REST
        API, return the authorized session. If rate limited, it means that the given
        PAT is valid and a usable connection has been made

        :rtype None:
        """

        def __read_auth_file(auth_file_path) -> str:
            """
            read personal access tokens (PATs) out of auth file

            :raises FileNotFoundError: file does not exist at path
            :param auth_file_path str: path to auth file
            :rtype pat_list list[str]: text lines from auth file
            """
            try:
                # attempt to open provided auth file path
                authfile_obj = open(auth_file_path, encoding="UTF-8")

            except FileNotFoundError:
                # if the file is not found log an error and exit
                no_auth_msg = (
                    "Authorization file not found! "
                    + "Please provide a valid file. Exiting...\n"
                )
                self.__logger.exception(no_auth_msg)
                sys.exit(1)

            else:
                self.__logger.info("Auth file found...\n")

                # read contents out of auth file object
                auth_text = authfile_obj.readline()

                authfile_obj.close()

                return auth_text.strip().strip("\n")

        # retrieve token from auth file
        token = __read_auth_file(auth_path)

        # establish a session with token
        session = github.Github(token, timeout=100, retry=100)

        try:
            # if name can be gathered from token, properly authenticated
            session.get_user().name

        # if token is not valid, remove token from list
        except github.BadCredentialsException:
            # log that token is invalid
            inval_token_msg = "Invalid personal access token found!\n"
            self.__logger.exception(inval_token_msg)
            sys.exit(1)

        except github.RateLimitExceededException:
            return session

        else:
            return session

    def print_rem_calls(self) -> None:
        """
        print remaining calls to API for this hour

        :rtype None: prints remaining calls
        """
        # get remaining calls before reset
        remaining_calls = self.session.rate_limiting[0]

        # format as a string
        rem_calls_str = f"{remaining_calls:<4d}"

        # clear line to erase any errors due to typing in the console
        print("", end="\r")

        # print output in place
        print(f"{' ' * 4}Calls left until sleep: {rem_calls_str}", end="\r")

    def sleep(self, msg_format=None):
        """
        sleep the program until we can make calls again

        :param msg_format str: optional message to print after sleeping
        """

        def __get_countdown_str():
            # modulo function returns time tuple
            minutes, seconds = divmod(countdown_time, 60)

            # format the time string before printing
            return f"{minutes:02d}:{seconds:02d}"

        def __get_countdown_time():
            # get time until reset
            reset_time_secs = self.session.rate_limiting_resettime

            # time to wait is the amount of seconds
            # until reset minus the current time
            return reset_time_secs - int(time.time())

        def __print_time_str():
            # clear line to erase any errors in console, such as
            # typing while the counter runs
            print("", end="\r")

            # print time string on the same line each decrement
            print(f"{' ' * 4}time until limit reset: {countdown_str}", end="\r")

        countdown_time = __get_countdown_time()

        while countdown_time > 0:

            countdown_str = __get_countdown_str()

            __print_time_str()

            # sleep for a while
            time.sleep(1)
            countdown_time -= 1

        # this allows us to choose to print a message after sleeping
        if msg_format is not None:
            self.__logger.info(msg_format)
