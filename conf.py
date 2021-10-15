# Author: MP


class cfg:

    def __init__( self, cfg_path, logger ) -> None:
        # intro: init cfg object for extractor object to hold onto and reference

        try:
            # get rest of config data
            self.__extract_cfg( cfg_path )

        except KeyError as key:
            key_err_msg = "\nFatal: Missing configuration for: " + str( key )
            logger.log( key_err_msg + '\n', "EXCEPT" )

        else:
            # loop through all configuration object members and
            # check if any is empty. If so, report it
            for key, val in vars( self ).items():
                if val == '':
                    no_val_err = "\nERROR: cfg key \"" + key + "\" has \
no associated value. Please check your configuartion."

                    logger.log( no_val_err, "ERR" )


    def __extract_cfg( self, cfg_file ) -> None:
        # read cfg file out into obj members

        try:
            conffile_obj = open( cfg_file, 'r' )

        except FileNotFoundError:
            print( "\nConfiguration file not found!" )

        else:
            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            conffile_obj.close()

            # clean cfg
            strip_list  = [ line.strip() for line in confinfo_list
                                if '-' not in line ]

            split_list  = [ line.split( '=' ) for line in strip_list
                                if line != '' ]

            cfg_dict    = { key.strip(): value.strip()
                            for ( key, value ) in split_list }


            # assign cfg items to self
            self.auth       = cfg_dict['auth_file']
            self.comm_json  = cfg_dict['commit_json']
            self.diag       = cfg_dict['diagnostics']
            self.issue_json = cfg_dict['issue_json']
            self.job        = cfg_dict['functionality']
            self.mast_json  = cfg_dict['master_json']
            self.pr_json    = cfg_dict['pr_json']
            self.repo       = cfg_dict['repo']
            self.rows       = cfg_dict['rows']
            self.text       = cfg_dict
