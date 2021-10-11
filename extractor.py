# Author: MP


# TODO
#  start extracting!
#  perfect logging


# modules
import github
import logger
import time


class extractor:

    def __init__( self, config_obj ) -> None:
        """ init extractor obj, which asks for, processes, and writes data """

        self.conf       = config_obj
        self.logger     = logger.ext_log( self.conf.log_path )

        self.__verify_auth()


    def __get_limit_info( self, type_flag ):

        out_rate_info = None


        if type_flag == "remaining":
            # get remaining calls before reset from GitHub API
            #   see rate_limiting docs for indexing details, e.g. "[0]"
            out_rate_info = self.sesh.rate_limiting[0]


        elif type_flag == "reset":
            # get time until reset as an integer
            reset_time_secs = self.sesh.rate_limiting_resettime

            # get the current time as an integer
            cur_time_secs = int( time.time() )

            # calculate the amount of time to sleep
            out_rate_info = reset_time_secs - cur_time_secs

        return out_rate_info


    def __sleep( self, msg_format ):

        def __timer( countdown_time ):

            while countdown_time > 0:
                # modulo function returns time tuple
                minutes, seconds = divmod( countdown_time, 60 )

                # format the time string before printing
                countdown_str = '{:02d}:{:02d}'.format( minutes, seconds )

                # clear line to erase any errors in console, such as typing while the
                # counter runs
                print( "", end='\r' )

                # print time string on the same line each decrement
                print( "        time until limit reset: " + countdown_str, end="\r" )

                time.sleep( 1 )
                countdown_time -= 1


        # print that we are sleeping
        self.logger.exe_log( "EXCEPT", "SLEEP" )

        # get the amount of time until our call amount is reset
        sleep_time = self.__get_limit_info( "reset" )

        # sleep for that amount of time
        __timer( sleep_time )

        print()

        # this allows us to choose to print a message after sleeping
        if msg_format is not None:
            self.logger.exe_log( "INFO", msg_format )


    def __verify_auth( self ) -> None:
        """ authenticate with PAT, init github connection """

        def read_auth( auth_file ) -> str:
            """ read personal access token out of auth file """

            try:
                authfile_obj = open( auth_file, 'r' )

            except FileNotFoundError:
                self.logger.exe_log( "ERROR", "NO_AUTH" )
                return "none"

            else:
                # read contents out of auth file object
                # this should be one line with a personal accss token ( PAT )
                authinfo_line = authfile_obj.readline()

                authfile_obj.close()

                # remove newline chars and surrounding whitespace from PAT
                return authinfo_line.strip().strip( '\n' )


        access_token = read_auth( self.conf.auth )

        if str.lower( access_token ) == "none":
            self.sesh = github.Github( timeout=100, retry=100 )

        # attempt to verify
        else:
            self.sesh = github.Github( self.conf.auth, timeout=100, retry=100 )

            try:
                self.sesh.get_user().name

            except github.BadCredentialsException:
                self.logger.exe_log( "EXCEPT", "INVAL_TOKEN" )
                self.sesh = github.Github( timeout=100, retry=100 )

            except github.RateLimitExceededException:
                self.__sleep( None )
                pass









