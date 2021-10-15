# Author: MP


import extractor


DASHES      = "-----------------------------------------------------------"
LOG_BAR     = DASHES + DASHES


def main():

    # init vars
    end_prog          = "END OF PROGRAM RUN\n" + LOG_BAR + '\n'
    prog_start_log    = '\n' + LOG_BAR + "\nSTART OF PROGRAM RUN"
    unspec_except_str = "\tUnspecified exception! Please see log file:\n\t"

    # init extractor object
    gh_reader = extractor.extractor()

    gh_reader.export_conf()

    # begin logging output
    gh_reader.logger.log( prog_start_log )


    try:
        exe_operation( gh_reader )

    except:
        gh_reader.logger.log( unspec_except_str +
                                gh_reader.logger.log_path + '\n', "EXCEPT" )

    else:
        gh_reader.logger.log( "\nOperations complete for repo \"" +
                                    gh_reader.cfg.repo + "\"." )

        print( "See " + gh_reader.logger.log_path + " for operation notes.\n" )

    finally:
        gh_reader.logger.log_obj.info( end_prog )




def exe_operation( extractor ):

    extractor.get_paged_list()






if __name__ == "__main__":
    main()

