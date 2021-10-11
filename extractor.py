# Author: MP

# TODO setup sleeping


# modules
import github


class extractor:

    def __init__( self, config_obj ) -> None:
        """ init extractor obj, which asks for, processes, and writes data """

        def verify_auth( self ) -> None:
            """ authenticate with PAT, init github connection """

            if str.lower( self.conf.auth ) == "none":
                self.sesh = github.Github( timeout=100, retry=100 )

            # attempt to verify
            else:
                self.sesh = github.Github( self.conf.auth, timeout=100, retry=100 )

                try:
                    self.sesh.get_user().name

                except github.BadCredentialsException:
                    # print
                    # OLD: log_and_print( "INVAL_TOKEN", "EXCEPT", logger )
                    print( "Invalid Personal Access Token!" )
                    self.sesh = github.Github( timeout=100, retry=100 )

                except github.RateLimitExceededException:
                    sleep( session, None, logger )




            return session


        self.conf   = config_obj
        self.sesh   = None




