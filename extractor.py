# Author: MP


# modules
import argparse
import conf
import github
import logger
import time
from utils import LOG_DICT


class extractor:
    # intro: extractor class acts as top-level actor in GitHub data extraction

    # Description: The extractor class contains and executes GitHub REST API
    # functionality. It holds onto a configuration object, initiates and
    # holds onto the connection to GitHub, asks for information from GitHub and
    # stores it in a dataset object, and has the ability to write that dataeset
    # to JSON or a database.

    # TODO
    # 1. data extraction methods
    # 2. data writing methods


    def __init__( self ) -> None:
        # intro: init extractor obj

        # Description: upon initialization, the configuration object is
        # created from the singular CLI arg. The logging obj is initialized
        # from information inside of that configuration obj. The dataset
        # object is instantiated but left unpopulated until a connection to
        # GitHub has been established

        def __get_CLI_args() -> str:

            # establish positional argument capability
            arg_parser = argparse.ArgumentParser( description="OSL Repo mining script" )

            # add repo input CLI arg
            arg_parser.add_argument( 'config_file', type=str, help="config file name" )

            # retrieve positional arguments
            return arg_parser.parse_args().config_file


        # get file name
        self.cfg_file   = __get_CLI_args();

        self.logger     = logger.ext_log( self.cfg_file )

        self.cfg        = conf.cfg( self.cfg_file, self.logger )

        self.dataset    = None
        self.sesh       = None

        # this function assigns member self.sesh internally
        self.__verify_auth()




    # Extraction functionality
    def get_paged_list( self ) -> None:
        try:
            # retrieve GitHub repo object
            repo_obj = self.sesh.get_repo( self.cfg.repo )

            if self.cfg.job in { "issues" }:
                self.logger.log( LOG_DICT["G_PAGED_ISSUES"] )

                self.issues_paged_list = repo_obj.get_issues( direction='asc',
                                                                sort='created',
                                                                    state='closed' )

            if self.cfg.job in { "pr" }:
                self.logger.log( LOG_DICT["G_PAGED_PR"] )

                self.pr_paged_list = repo_obj.get_pulls( direction='asc',
                                                            sort='created',
                                                                state='closed' )

            self.__print_rem_calls()

            self.logger.log_complete()


        except github.RateLimitExceededException:
            print()
            self.__sleep( LOG_DICT["G_MORE_PAGES"] )




    # Authentication functionality
    def __verify_auth( self ) -> None:
        # authenticate with PAT, init GitHub connection

        def __read_auth( auth_file ) -> str:
            # intro: read personal access token out of auth
            #        file given as config option

            try:
                authfile_obj = open( auth_file, 'r' )

            except FileNotFoundError:
                self.logger.log( LOG_DICT["NO_AUTH"], "ERR" )
                return "none"

            else:
                # read contents out of auth file object
                # this should be one line with a personal accss token ( PAT )
                authinfo_line = authfile_obj.readline()

                authfile_obj.close()

                # remove newline chars and surrounding whitespace from PAT
                return authinfo_line.strip().strip( '\n' )


        access_token = __read_auth( self.cfg.auth )

        # if the user provides "none", use unauthenticated connection
        if str.lower( access_token ) == "none":
            self.sesh = github.Github( timeout=100, retry=100 )

        # attempt to verify
        else:
            self.sesh = github.Github( access_token, timeout=100, retry=100 )

            try:
                # if name can be gathered from token, properly authenticated
                # see https://pygithub.readthedocs.io/en/latest/github_objects/AuthenticatedUser.html
                self.sesh.get_user().name

            except github.BadCredentialsException:
                # log that token is invalid
                self.logger.log( LOG_DICT["INVAL_TOKEN"], "EXCEPT" )

                # use unauthenticated connection
                self.sesh = github.Github( timeout=100, retry=100 )

            except github.RateLimitExceededException:
                self.__sleep( None )




    # Display functionality
    def export_conf( self ) -> None:
        # print the configuration provided in conf CLI arg

        log_str = "\nProvided configuration:\n"

        for key, val in self.cfg.text.items():
            log_str += '\t' + key + ": " + val + '\n'

        self.logger.log_obj.info( log_str )




    # GitHub connection management functionality
    def __print_rem_calls( self ):
        # print remaining calls to API for this hour

        # get remaining calls before reset
        remaining_calls = self.sesh.rate_limiting[0]

        # format as a string
        rem_calls_str = '{:<4d}'.format( remaining_calls )

        # clear line to erase any errors due to typing in the console
        print( "", end='\r' )

        # print output in place
        print( "    Calls left until sleep: " + rem_calls_str, end='\r' )
        print( '\n' )


    def __sleep( self, msg_format ):
        # sleep the program until we can make calls to API again

        def __timer():

            # get time until reset
            reset_time_secs = self.sesh.rate_limiting_resettime

            # time to wait is the amount of seconds
            # until reset minus the current time
            countdown_time = reset_time_secs - int( time.time() )

            while countdown_time > 0:

                # modulo function returns time tuple
                minutes, seconds = divmod( countdown_time, 60 )

                # format the time string before printing
                countdown_str = '{:02d}:{:02d}'.format( minutes, seconds )

                # clear line to erase any errors in console, such as
                # typing while the counter runs
                print( "", end='\r' )

                # print time string on the same line each decrement
                print( "    time until limit reset: " + countdown_str, end="\r" )

                # sleep for a while
                time.sleep( 1 )
                countdown_time -= 1


        # print that we are sleeping
        self.logger.log( LOG_DICT["SLEEP"], "EXCEPT" )

        # sleep for the amount of time until our call amount is reset
        __timer()

        print()

        # this allows us to choose to print a message after sleeping
        if msg_format is not None:
            self.logger.log( msg_format )



