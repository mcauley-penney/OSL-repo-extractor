#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 


from . import cfg 
from . import cli_ops 
from . import io_ops
from . log_ops import complete, init_logger, log_and_print  
from . import mine_ops
from . timer_ops import sleep
import github



#--------------------------------------------------------------------------- 
# Function name : driver
# Process       : gathers args from commandline, reads user info out of file,
#                 authenticates the user with GitHub, retrieves paginated
#                 lists of relevant info for mining, and sends those lists to
#                 be mined and the mined info written
# Parameters    : none
# Postconditions: CSV files with relevant info are produced in the current
#                 directory
# Notes         : none
# Other Docs    :
#                 - topic: github class: 
#                   -link: https://pygithub.readthedocs.io/en/latest/github.html
#--------------------------------------------------------------------------- 
def main():
     
    # init vars
    end_prog = '\n' + "END OF PROGRAM RUN" + '\n' + cfg.LOG_BAR

    # retrieve positional arguments as variables
    config_file_name = cli_ops.get_CLI_args()

    # get prog run info
    conf_list = cli_ops.read_config( config_file_name ) 

    # establish logging capabilities
    log_filename = conf_list[7]
    logger       = init_logger( log_filename )  

    # authenticate the user with GitHub and insert session into list
    auth_token    = conf_list[-1]
    session       = github.Github( auth_token, timeout=100, retry=100 ) 
    conf_list[-1] = session

    try:
        exe_menu( conf_list, logger )

    except:
        logger.exception( cfg.NL_TAB + "Unspecified exception:\n\n" )

        print( '\n' + cfg.EXCEPT_MSG )
        print( cfg.TAB  + "Unspecified exception! Please see log file!" )

    finally:
        logger.info( end_prog )  




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def exe_menu( conf_list, logger ):

    # gather config values
    repo_str             = conf_list[1]
    row_quant            = conf_list[3]
    issue_state          = conf_list[4]
    pr_state             = conf_list[5] 
    diagnostics          = conf_list[6]

    issue_json_filename  = conf_list[8]
    pr_json_filename     = conf_list[9]
    commit_json_filename = conf_list[10]
    master_json_filename = conf_list[11]

    pr_csv_filename      = conf_list[12]
    commit_csv_filename  = conf_list[13]
    session              = conf_list[-1]
    

    # init other vars
    conf_tuple = tuple( conf_list[0:-1] )

    csv_prompt = """
Please choose type of CSV:                                      
    [1] Pull Request
    [2] Commit
    [3] Both

    Execute """  
    
    header = """ 
    PROGRAM START
    -------------

    Config used: 
        - config file name : %s
        - repo             : %s
        - auth file        : %s
        - rows             : %s
        - issue state      : %s        
        - pr state         : %s          
        - diagnostics      : %s          
        - log file         : %s        

        - issue json file  : %s
        - pr JSON file     : %s
        - commit JSON file : %s
        - master JSON file : %s

        - "pr" CSV file    : %s       
        - "commit" CSV file: %s
"""

    prog_intro = """
GITHUB REPO EXTRACTOR
---------------------

Please choose type of operation:                                      
    [1] get issue JSON list
    [2] get pull request and commit JSON lists
    [3] get all three relevant lists
    [4] collate JSON lists into unified JSON list
    [5] compile CSV outputs

    Execute """


    log_header = header %( conf_tuple )

    if diagnostics == "true":
        print( '\n' + cfg.DIAG_MSG + '\n' + log_header )

    logger.info( log_header )

    # get operation choice
    op_choice = input( prog_intro )


    # enact choice
    if op_choice == "1" or op_choice == "2" or op_choice == "3": 

        try:
            session.get_user().name

        except github.BadCredentialsException:
            log_and_print( "INVAL_TOKEN", "EXCEPT", logger ) 

        except github.RateLimitExceededException:
            sleep( session, None, logger )

        else:
            if diagnostics == "true":
                print( '\n' + cfg.DIAG_MSG + "Personal Access Token valid!" )


            log_and_print( "PROG_START", "INFO", logger )

            paged_metalist = mine_ops.get_paginated_lists( session, repo_str, 
                                                           logger, pr_state, 
                                                           issue_state, op_choice )

            issue_paged_list, pr_paged_list = paged_metalist 

            if op_choice == "1" or op_choice == "3": 
                issue_metalist = mine_ops.get_issue_info( session, 
                                                          issue_paged_list, 
                                                          row_quant, diagnostics,
                                                          logger )

                io_ops.write_json( issue_metalist, issue_json_filename,
                                   "W_JSON_ISSUE", logger )
             

            if op_choice == "2" or op_choice == "3":

                # get metalist of pr information and commit info paginated list
                #   We get the commit paginated lists here because it allows us
                #   to segment each group of commits into their own lists. It 
                #   is possible to retrieve a monolithic list of commits from 
                #   the github object but they would not be broken up by PR
                list_tuple = mine_ops.get_PR_info( session, pr_paged_list, 
                                                   row_quant, diagnostics, logger ) 

                pr_metalist, commits_py_list = list_tuple

                io_ops.write_json( pr_metalist, issue_json_filename,
                                   "W_JSON_PR", logger )


                commit_metalist = mine_ops.get_commit_info( session, 
                                                            commits_py_list, 
                                                            logger )

                io_ops.write_json( commit_metalist, commit_json_filename,
                                   "W_JSON_COMMIT", logger )


            elif op_choice == "4": 

                log_and_print( "PROG_START", "INFO", logger )

                json_file_list = [
                        issue_json_filename, 
                        pr_json_filename, 
                        commit_json_filename,
                        master_json_filename
                        ]

                # turn py lists into one list and write to JSON
                io_ops.create_master_json( json_file_list, logger )


            elif op_choice == "5": 

                csv_choice = input( csv_prompt )

                log_and_print( "PROG_START", "INFO", logger )

                master_info_list = io_ops.read_json( master_json_filename, "R_JSON_ALL" ,
                                                     logger )


                if csv_choice == "1" or csv_choice == "3":
                    log_and_print( "W_CSV_PR", "INFO", logger )
                    io_ops.write_pr_csv( master_info_list, pr_csv_filename )
                    complete( logger )


                if csv_choice == "2" or csv_choice == "3":
                    log_and_print( "W_CSV_COMMIT", "INFO", logger )
                    io_ops.write_commit_csv( master_info_list, commit_csv_filename )
                    complete( logger ) 




if __name__ == "__main__":
    main()  





