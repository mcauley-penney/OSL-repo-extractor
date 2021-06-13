# ---------------------------------------------------------------------------
# Authors: Jacob Penney
# Notes  : documentation for pygithub can be found @
#          https://pygithub.readthedocs.io/en/latest/index.html
# --------------------------------------------------------------------------- 


# DOC IDEAS
#   - discuss branches and how they can determine data grabbed
#       - how master and main may be available even though not shown


# imports
import argparse
import csv
import github
import json
import logging
import os
import time


# constants
DASHES= "-----------------------------------------------------------"
BKBLU     = "\033[1;38;5;15;48;2;0;111;184m"  
BKGRN     = "\033[1;38;5;0;48;2;16;185;129m"  
BKRED     = "\033[1;38;5;0;48;2;240;71;71m"  
BKYEL     = "\033[1;38;5;0;48;2;251;191;36m"  
NAN       = "NaN"
NL        = '\n'
TXTRST    = "\033[0;0m" 
TAB       = "    "
TIME_FRMT = "%D, %I:%M:%S %p"

LOG_BAR     = DASHES + DASHES
DIAG_MSG    = TAB + BKYEL +" [Diagnostics]: " + TXTRST + ' ' 
NL_TAB      = NL + TAB
INFO_MSG    = NL_TAB + BKBLU + " Info: " + TXTRST
ERR_MSG     = NL_TAB + BKRED + " Error: " + TXTRST
EXCEPT_MSG  = NL_TAB + BKRED + " Exception: " + TXTRST




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
    end_prog = NL + "END OF PROGRAM RUN" + NL + LOG_BAR
    unspec_except_str = TAB  + "Unspecified exception! Please see "

    # retrieve positional arguments as variables
    config_file_name = get_CLI_args()

    # get prog run info
    conf_list = read_config( config_file_name ) 

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
        logger.exception( NL_TAB + "Unspecified exception:\n\n" )


        print( NL + EXCEPT_MSG )
        print( unspec_except_str + log_filename + "!" )

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
def check_row_quant_safety( paged_list, config_quant, msg, logger ):

    # init vars
    output_quant    = 0
    stripped_quant  = config_quant.strip()
    str_param_quant = str.lower( stripped_quant )
    
    log_and_print( msg, "INFO", logger )

    # if all rows are desired or the desired amount is more than exists, adjust
    if str_param_quant == "all" or int( config_quant ) > paged_list.totalCount:
       output_quant = int( paged_list.totalCount )

    elif int( config_quant ) <= paged_list.totalCount:
        output_quant = int( config_quant ) 

    else:
        log_and_print( "INVAL_ROW", "ERROR", logger )


    complete( logger )


    return output_quant




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def collate_py_lists( info_metalist ): 
    
    # unpack list of metalists
    issue_metalist  = info_metalist[0]
    pr_metalist     = info_metalist[1]
    commit_metalist = info_metalist[2]

    # init other vars
    issue_index    = 0
    issue_list_len = len( issue_metalist ) 
    pr_index       = 0
    pr_list_len    = len( pr_metalist )


    while issue_index < issue_list_len:

        # reset vars
        isPR = 0

        # get issue and PR nums to line up values
        issue_num = issue_metalist[issue_index][0]
        pr_num    = pr_metalist[pr_index][0]                   

        if issue_num == pr_num:

            isPR = 1

            # append entire lists to issue list:
            #   this forces all PR and commit info into singular indices in the
            #   issue list
            issue_metalist[issue_index].append( pr_metalist[pr_index] )
            issue_metalist[issue_index].append( commit_metalist[pr_index] )

            if pr_index < pr_list_len - 1 :
                pr_index += 1 


        issue_metalist[issue_index].append( isPR )

        issue_index += 1


    return issue_metalist




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def complete( logger ):

    log_and_print( "COMPLETE", "INFO", logger )




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def create_master_json( json_file_list, logger ):

    # unpack list of JSON file names to read
    issue_json_filename  = json_file_list[0]
    pr_json_filename     = json_file_list[1]
    commit_json_filename = json_file_list[2]
    master_json_filename = json_file_list[3]


    # read metalists out of JSON storage
    issue_info_list  = read_json( issue_json_filename, "R_JSON_ISSUE", logger )
    pr_info_list     = read_json( pr_json_filename, "R_JSON_PR", logger )
    commit_info_list = read_json( commit_json_filename, "R_JSON_COMMIT", logger )


    # get list of python lists
    info_metalist = [issue_info_list, pr_info_list, commit_info_list] 
    

    # put all data content into one list
    log_and_print( "COLLATE", "INFO", logger )
    collated_list = collate_py_lists( info_metalist )
    complete( logger )


    # write that list to JSON 
    write_json( collated_list, master_json_filename, "W_JSON_ALL", logger )




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
        print( NL + DIAG_MSG + NL + log_header )

    logger.info( log_header )

    # get operation choice
    op_choice = input( prog_intro )

    # enact choice
    if op_choice in { "1", "2", "3" }:

        try:
            session.get_user().name

        except github.BadCredentialsException:
            log_and_print( "INVAL_TOKEN", "EXCEPT", logger ) 

        except github.RateLimitExceededException:
            sleep( session, None, logger )

        else:
            if diagnostics == "true":
                print( NL + DIAG_MSG + "Personal Access Token valid!" )


            log_and_print( "PROG_START", "INFO", logger )

            paged_metalist = get_paginated_lists( session, repo_str, logger, 
                                                  pr_state, issue_state, op_choice )

            issue_paged_list, pr_paged_list = paged_metalist 


            if op_choice in { "1", "3" }: 
                issue_metalist = get_issue_info( session, issue_paged_list, 
                                                 row_quant, diagnostics, logger )

                write_json( issue_metalist, issue_json_filename, "W_JSON_ISSUE",
                            logger ) 
             

            if op_choice in { "2", "3" }: 

                # get metalist of pr information and commit info paginated list
                #   We get the commit paginated lists here because it allows us
                #   to segment each group of commits into their own lists. It 
                #   is possible to retrieve a monolithic list of commits from 
                #   the github object but they would not be broken up by PR
                list_tuple = get_PR_info( session, pr_paged_list, row_quant, 
                                          diagnostics, logger ) 

                pr_metalist, commit_py_metalist, unmerged_pr_str = list_tuple

                write_json( pr_metalist, issue_json_filename, "W_JSON_PR", 
                            logger )

                commit_metalist, diag_strs = get_commit_info( session, 
                                                               commit_py_metalist, 
                                                               logger )

                write_json( commit_metalist, commit_json_filename, 
                            "W_JSON_COMMIT", logger ) 

                # log commit diagnostic information
                logger.info( unmerged_pr_str )
                logger.info( diag_strs[0] )
                logger.info( diag_strs[1] )


    if op_choice == "4": 

        log_and_print( "PROG_START", "INFO", logger )

        json_file_list = [
                issue_json_filename, 
                pr_json_filename, 
                commit_json_filename,
                master_json_filename
                ]

        # turn py lists into one list and write to JSON
        create_master_json( json_file_list, logger )


    if op_choice == "5": 

        csv_choice = input( csv_prompt )

        log_and_print( "PROG_START", "INFO", logger )

        master_info_list = read_json( master_json_filename, 
                                      "R_JSON_ALL", logger ) 

        if csv_choice in { "1", "3" }:
            log_and_print( "W_CSV_PR", "INFO", logger )
            write_csv( master_info_list, pr_csv_filename, "pr" )
            # write_pr_csv( master_info_list, pr_csv_filename )
            complete( logger )


        if csv_choice in { "1", "3" }:
            log_and_print( "W_CSV_COMMIT", "INFO", logger )
            write_csv( master_info_list, commit_csv_filename, "commit" )
            # write_commit_csv( master_info_list, commit_csv_filename )
            complete( logger )




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#---------------------------------------------------------------------------  
def filter_commits( session, commit_py_metalist, logger ):

    index = 0

    commit_info_list       = []
    no_commit_str          = NL_TAB + "Pull Requsts with No Commits:"
    no_changed_file_str    = NL_TAB + "Commits with no changed files:"

    commit_py_metalist_len = len( commit_py_metalist )


    log_and_print( "F_COMMIT", "INFO", logger )
 
    while index < commit_py_metalist_len:

        # reset vars
        most_recent_commit = NAN

        try:
            cur_commit_pr_num     = commit_py_metalist[index][0]
            cur_commit_paged_list = commit_py_metalist[index][1]

            num_of_commits = cur_commit_paged_list.totalCount

            # test if this PR has commits          
            # if not, we do not want to include it and will instead put it on
            # a list for diagnostics
            if num_of_commits > 0:

                # get index of last commit                
                last_commit_position = num_of_commits - 1 

                # store most recent\last commit                           
                commit_of_interest = cur_commit_paged_list[last_commit_position]

                # check if the commit has changed files and document if not
                commit_files        = commit_of_interest.files         
                num_of_commit_files = len( commit_files )              
                                                                       
                if num_of_commit_files > 0:                            
                    most_recent_commit = commit_of_interest            

                else: 
                    no_changed_file_str += NL_TAB + TAB + cur_commit_pr_num


            else:
                no_commit_str += NL_TAB + TAB + cur_commit_pr_num


        except github.RateLimitExceededException:
            print()
            sleep( session, "F_MORE_COMMIT", logger ) 

        else:
            commit_info_list.append( most_recent_commit )

            print_rem_calls( session )

            index += 1


    diagnostics_lists = no_commit_str, no_changed_file_str

    complete( logger )


    return commit_info_list, diagnostics_lists




#--------------------------------------------------------------------------- 
# Function name: get_CLI_args 
# Process      : adds the ability to process commandline args and a grouping
#                of mutually exclusive args, collects and processes the args,
#                and returns them to the user
# Parameters   : none
# Output       : 
#                - name  : config_file
#                  - type: str
#                  - desc: str containing name of config file
#                  - docs: none
# Notes        : none
# Docs         : 
#                - topic: argparse (library)
#                  - link: https://docs.python.org/3/library/argparse.html
#--------------------------------------------------------------------------- 
def get_CLI_args():

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="OSL Repo mining script" )
    
    # add repo input CLI arg
    arg_parser.add_argument( 'config_file', type=str, help="config file name" ) 

    # retrieve positional arguments
    config_file_name = arg_parser.parse_args().config_file


    return config_file_name




#--------------------------------------------------------------------------- 
# Function name: get_commit_info
# Process      : receives list of chronologically most recent commits as
#                commit objects and extracts relevant info from them
# Parameters   : 
#                - name  : commit_list
#                  - type: Python list of pygithub commit objects
#                  - desc: list of commit objects containing relevant commit
#                          info
#                  - docs: https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html
#                - name  : session 
#                  - type: pygithub "Github" object                       
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library 
#                  - docs: https://pygithub.readthedocs.io/en/latest/github.html 
#                - name  : output_type                       
#                  - type: str                               
#                  - desc: one of two formats for CSV output 
# Output       : 
#                 - name  : commit_info_metalist
#                   - type: Python list of python lists
#                   - desc: each index contains a list of varying types of
#                           data associated with a commit, itself associated
#                           with a PR at the same index in the output of
#                           get_PR_info()
#                   - docs:  
#                     - topic : pygithub commit object
#                       - link: https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html
# Notes        : empty fields should be caught and populated with " =||= "
# Other Docs   : none
#--------------------------------------------------------------------------- 
def get_commit_info( session, commit_py_metalist, logger ):

    # init other vars
    index      = 0

    commit_file_list       = [] 
    commit_metalist        = []


    commit_list, diag_lists = filter_commits( session, commit_py_metalist,
                                                   logger )

    commit_info_list_len = len( commit_list )


    log_and_print( "G_DATA_COMMIT", "INFO", logger )

    while index < commit_info_list_len:
        try:
             
            # reset variables
            commit_author_name       = NAN
            commit_message           = NAN
            commit_date              = NAN
            commit_committer         = NAN
            commit_SHA               = NAN
            commit_file_list         = NAN
            commit_patch_text        = NAN
            commit_adds              = NAN
            commit_removes           = NAN
            quoted_commit_status_str = NAN
            commit_changes           = NAN 

            commit_adds          = 0
            commit_changes       = 0
            commit_file_list     = []
            commit_patch_text    = ""
            commit_removes       = 0
            commit_status_str    = "" 

            # retrieve list of commits for one pr
            cur_commit = commit_list[index] 

            if cur_commit != NAN:

                commit_author      = cur_commit.commit.author
                commit_author_name = commit_author.name
                commit_message     = cur_commit.commit.message
                commit_date        = commit_author.date.strftime( TIME_FRMT )
                commit_committer   = cur_commit.commit.committer.name 
                commit_SHA         = cur_commit.sha 
                commit_files       = cur_commit.files 

                # retrieve each modified file and place in list
                for file in commit_files:
                    commit_file_list.append( file.filename )
                    commit_adds       += int( file.additions )
                    commit_changes    += int( file.changes )
                    commit_patch_text += str( file.patch ) + ", "
                    commit_removes    += int( file.deletions )
                    commit_status_str += str( file.status ) + ", "

                
                quoted_commit_status_str = "\"" + commit_status_str + "\"" 


            commit_info_list = [
                    commit_author_name, 
                    commit_message,
                    commit_date,  
                    commit_committer,
                    commit_SHA, 
                    commit_file_list, 
                    commit_patch_text,
                    commit_adds,
                    commit_removes,
                    quoted_commit_status_str,
                    commit_changes
                    ]


            # append list of collected commit info to metalist
            commit_metalist.append( commit_info_list )

            # print remaining calls per hour
            print_rem_calls( session )

            index += 1


        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_COMMIT", logger )


    complete( logger )

    return commit_metalist, diag_lists




#--------------------------------------------------------------------------- 
# Function name: get_issue_info
# Process      : receives paginated list of issues associated with the given
#                repo and extracts relevant info
# Parameters   : 
#                - name  : issue_list
#                  - type: paginated list of pygithub issue objects
#                  - desc: none
#                  - docs: 
#                     - topic : pygithub issue objects
#                       - link: https://pygithub.readthedocs.io/en/latest/github_objects/Issue.html
#                - name  : session 
#                  - type: pygithub "Github" object                       
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library 
#                  - docs: https://pygithub.readthedocs.io/en/latest/github.html
# Output       : 
#                 - name  : issue_metalist
#                   - type: Python list of python lists
#                   - desc: each index contains a list of relevant issue info
#                   - docs: none
# Notes        : This function is only used by the "-p"/"--pr" output_type
#                option
# Other Docs   :
#                - topic : checking for NoneType 
#                  - link: https://stackoverflow.com/questions/23086383/how-to-test-nonetype-in-python 
#                 - topic : paginated lists
#                   - link: https://docs.github.com/en/rest/guides/traversing-with-pagination
#                   - link: https://pygithub.readthedocs.io/en/latest/utilities.html#github.PaginatedList.PaginatedList
#--------------------------------------------------------------------------- 
def get_issue_info( session, issue_paged_list, row_quant, diagnostics, logger ):
    
    # init vars 
    index           = 0
    issue_info_list = []
    issue_metalist  = []


    safe_quant = check_row_quant_safety( issue_paged_list, row_quant,
                                         "V_ROW_#_ISSUE", logger )

    log_and_print( "G_DATA_ISSUE", "INFO", logger )

    if diagnostics == "true":
        print( NL_TAB + DIAG_MSG )


    while index < safe_quant:
        try:

            # reset vars 
            issue_comment_str = ""  

            # work on one issue from paginated list at a time
            cur_issue         = issue_paged_list[index]          
            cur_issue_user    = cur_issue.user

            # get info from curret issue
            issue_num       = str( cur_issue.number )
            issue_title_str = cur_issue.title
            issue_name_str  = cur_issue_user.name
            issue_login_str = cur_issue_user.login
            issue_body_str  = cur_issue.body

            # protect code from failure if chosen issue state is not "closed"
            if cur_issue.closed_at is not None:
                closed_date_obj = cur_issue.closed_at
                issue_closed_date = closed_date_obj.strftime( TIME_FRMT )
            
            else:
                issue_closed_date = NAN


            # get issue comment at last position
            comments_paged_list = cur_issue.get_comments() 

            
            if comments_paged_list.totalCount == 0:
                issue_comment_str = NAN

            else:
                for comment in comments_paged_list:
                    issue_comment_str += comment.body + " =||= "


            if issue_name_str == "":
                issue_name_str = NAN


            if issue_login_str == "":
                issue_login_str = NAN


            if issue_body_str is None or issue_body_str == "":
                issue_body_str = NAN

            else:
                issue_body_str = issue_body_str.strip( '\n' )  


            issue_info_list = [
                    issue_num,
                    issue_title_str,
                    issue_name_str, 
                    issue_login_str,
                    issue_closed_date, 
                    issue_body_str,
                    issue_comment_str,
                    ]

        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_ISSUE", logger )

        else:
            issue_metalist.append( issue_info_list )

            if diagnostics == "true":

                issue_list_len     = str( len( issue_metalist ))
                row_quant_str      = str( safe_quant )
                
                print( "\n\n        Issue num             : " + issue_num )
                print( "        Length of issue list  : " + issue_list_len
                        + "/" + row_quant_str )
                                          

            print_rem_calls( session )
            index += 1 


    complete( logger )

    return issue_metalist





#--------------------------------------------------------------------------- 
# Function name: get_limit_info
# Process      : uses type_flag param to determine type of output to user;
#                returns info relevant to authenticated session resources
# Parameters   : 
#                - name  : session
#                  - type: pygithub "Github" object
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library
#                  - docs: https://pygithub.readthedocs.io/en/latest/github.html
#                - name  : type_flag
#                  - type: str
#                  - desc: contains the type of output asked for by the user;
#                          can be:
#                          - "remaining": returns remaining calls to GitHub API
#                                         before session is rate limited.
#                                         Resulting attribute (rate_limiting) 
#                                         belongs to "Github" class
#                          - "reset": returns the amount of time before amount 
#                                     of calls to GitHub API is renewed. Always 
#                                     starts at one hour. Resulting attribute 
#                                     (rate_limiting_resettime) belongs to 
#                                     "Github" class 
#                  - docs: 
#                     - topic : Pygithub authenticated session class
#                       - link: https://pygithub.readthedocs.io/en/latest/github.html
# Output       : 
#                 - name  : out_rate_info
#                   - type: int
#                   - desc: if "remaining", contains remaining requests for
#                           the current hour for the current authenticated 
#                           session. if "reset", the amount of time in seconds 
#                           before API calls are reset to full value
#                   - docs: none
# Notes        : none
# Other Docs   : none
#--------------------------------------------------------------------------- 
def get_limit_info( session, type_flag ):

    out_rate_info = None


    if type_flag == "remaining":

        # get remaining calls before reset from GitHub API
        #   see rate_limiting docs for indexing details, e.g. "[0]"
        out_rate_info = session.rate_limiting[0]
    
    elif type_flag == "reset":

        # get time until reset as an integer
        reset_time_secs = session.rate_limiting_resettime

        # get the current time as an integer
        cur_time_secs = int( time.time() )

        # calculate the amount of time to sleep
        out_rate_info = reset_time_secs - cur_time_secs 


    return out_rate_info




#--------------------------------------------------------------------------- 
# Function name: get_paginated_lists
# Process      : uses CLI str arg of repo name during call to GitHub to 
#                retrieve pygithub repo object, uses repo object in call to 
#                retrieve paginated list of all pull requsts associated with 
#                that repo, and all associated issues depending on the output
#                file desired
# Parameters   : 
#                - name  : input_repo_str
#                  - type: str 
#                  - desc: commandline arg containing repo name
#                - name  : output_type
#                  - type: str
#                  - desc: one of two formats for CSV output
#                - name  : session
#                  - type: pygithub "Github" object
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library
#                  - docs: 
#                    - topic : pygithub Github objects 
#                      - link: https://pygithub.readthedocs.io/en/latest/github.html
# Output       : 
#                - name  : issue_list
#                  - type: paginated list of pygithub issue objects
#                  - desc: none
#                  - docs: 
#                     - topic : pygithub issue objects
#                       - link: https://pygithub.readthedocs.io/en/latest/github_objects/Issue.html
#                 - name  : pr_list
#                   - type: paginated list of pygithub pull request objects 
#                   - desc: none
#                   - docs: 
#                     - topic : pygithub pull request objects
#                       - link: https://pygithub.readthedocs.io/en/latest/github_objects/PullRequest.html
# Notes        : utilizes try-except block to preempt code breaking due to
#                exception thrown for rate limiting
#                  - docs: https://pygithub.readthedocs.io/en/latest/utilities.html
# Other Docs   : 
#                 - topic : pygithub repo objects
#                   - link: https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
#--------------------------------------------------------------------------- 
def get_paginated_lists( session, repo_str, logger, pr_state, issue_state, 
                         op_choice ):

    # init vars 
    all_lists_retrieved = False
    issues_list         = []
    output_list         = []
    pr_list             = [] 

   
    # loop until both lists are fully retrieved
    while all_lists_retrieved == False:
        try:
            # retrieve GitHub repo object
            repo_obj = session.get_repo( repo_str )   


            if op_choice == "1" or op_choice == "3":
                
                log_and_print( "G_PAGED_ISSUES", "INFO", logger )

                issues_list = repo_obj.get_issues( direction='asc',
                                                    sort='created', 
                                                    state=issue_state )

                print_rem_calls( session )

                complete( logger )


            if op_choice == "2" or op_choice == "3":

                log_and_print( "G_PAGED_PR", "INFO", logger )
                
                pr_list = repo_obj.get_pulls( direction='asc',
                                              sort='created', state=pr_state )  

                print_rem_calls( session )

                complete( logger )


            output_list = [issues_list, pr_list]

            all_lists_retrieved = True

        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_PAGES", logger )


    return output_list 





#--------------------------------------------------------------------------- 
# Function name: get_PR_info
# Process      : creates list of relevant pull request info, depending on type
#                of output CSV desired, via calls to GitHub API 
# Parameters   : 
#                - name  : pr_list
#                  - type: paginated list of pygithub pull request objects 
#                  - desc: none
#                  - docs: 
#                    - topic : pygithub pull request objects
#                      - link: https://pygithub.readthedocs.io/en/latest/github_objects/PullRequest.html 
#                - name  : session
#                  - type: pygithub "Github" object
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library
#                  - docs: 
#                    - topic : pygithub Github objects
#                      - link: https://pygithub.readthedocs.io/en/latest/github.html 
#                - name  : output_type
#                  - type: str
#                  - desc: one of two formats for CSV output 
# Output       : 
#                 - name  : pr_metalist
#                   - type: Python list of python lists
#                   - desc: each index is a list of info related to a pr in
#                           the input repo
#                   - docs: none
#                 - name  : commit_list
#                   - type: Python list of pygithub commit objects
#                   - desc: list of commit objects containing relevant commit
#                           info
#                   - docs: https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html#github.Commit.Commit 
# Notes        : get_commit_info() depends on the paginated list of commits 
#                output from this function, as opposed to get_paginated_lists().
#                This is because I wanted to make sure that I was retrieving a 
#                list of commits specifically associated with the pr's I would 
#                gather here.
# Other Docs   : none
#--------------------------------------------------------------------------- 
def get_PR_info( session, pr_paged_list, row_quant, diagnostics, logger ):

    # init variables
    index           = 0

    commits_list    = []
    pr_metalist     = []
    unmerged_pr_str = NL_TAB + "Non-merged Pull Requests:"

    # diagnostics strings
    commit_list_len_diag = "        Length of commits list: "
    # commits_per_pr_diag  = "        Number of commits/pr  : " 
    pr_list_len_diag     = "        Length of pr lists    : " 
    pr_num_diag          = "\n\n        PR num                : "


    safe_quant = check_row_quant_safety( pr_paged_list, row_quant, 
                                         "V_ROW_#_PR", logger )

    log_and_print( "G_DATA_PR", "INFO", logger )

    if diagnostics == "true":
        print( NL_TAB + DIAG_MSG )

    while index < safe_quant:

        # reset vars
        pr_title_str       = NAN
        pr_author_name     = NAN 
        pr_author_login    = NAN 
        pr_closed_date_str = NAN
        pr_body_str        = NAN
        pr_comment_str     = NAN 

        cur_pr         = pr_paged_list[index]
        cur_pr_commits = NAN

        try:
            pr_num_str = str( cur_pr.number )

            if cur_pr.merged == True:
                try:
                    cur_pr_user = cur_pr.user

                    pr_title_str    = cur_pr.title
                    pr_author_name  = cur_pr_user.name
                    pr_author_login = cur_pr_user.login
                    pr_body_str     = cur_pr.body 

                    if pr_title_str == "":
                        pr_title_str = NAN 


                    #  clean each pr body of new line chars and place in quotes
                    if pr_body_str is None or pr_body_str == "":
                        pr_body_str = NAN

                    else:
                        pr_body_str = pr_body_str.strip( '\n' )


                    if cur_pr.closed_at is not None:
                       pr_closed_date_str = cur_pr.closed_at.strftime( TIME_FRMT )


                    pr_info_list = [
                            pr_num_str,
                            pr_title_str,
                            pr_author_name,
                            pr_author_login,
                            pr_closed_date_str,
                            pr_body_str,
                            pr_comment_str
                            ]

                    # get paginated list of commits for each merged PR
                    cur_pr_commits = pr_num_str, cur_pr.get_commits() 


                except github.RateLimitExceededException:
                    print()
                    sleep( session, "G_MORE_PR", logger )


                else:
                    # append each list of pr info to a metalist
                    pr_metalist.append( pr_info_list ) 

                    # append paginated list of commits to list
                    commits_list.append( cur_pr_commits ) 

                    # display info
                    if diagnostics == "true":

                        commit_list_len    = str( len( commits_list ))
                        pr_list_len        = str( len( pr_metalist ))
                        row_quant_str      = str( safe_quant )

                        print( pr_num_diag + pr_num_str )
                        print( pr_list_len_diag + pr_list_len + '/' + row_quant_str )
                        print( commit_list_len_diag + commit_list_len + '/' + row_quant_str)


                    print_rem_calls( session )

                    index += 1 


            else:
                unmerged_pr_str += NL_TAB + TAB + pr_num_str
                index += 1 


        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_PR", logger )


    complete( logger )

    print( unmerged_pr_str )

    return pr_metalist, commits_list, unmerged_pr_str
 



#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def init_logger( log_file_name ):

    log_msg_format  = "\n%(asctime)s: %(message)s"
    log_time_format = "%a, " + TIME_FRMT

    # create logger
    logger = logging.getLogger( __name__ )

    # create file handling
    verify_dirs( log_file_name )
    out_file_handler = logging.FileHandler( log_file_name )

    # create formatting
    formatter = logging.Formatter( log_msg_format, log_time_format )
    out_file_handler.setFormatter( formatter )

    # set log level
    logger.setLevel( logging.INFO )

    # set handler
    logger.addHandler( out_file_handler )


    return logger



#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def json_io( file_path, mode, output_py_metalist ):

    output = False


    # write JSON string to file
    with open( file_path, mode ) as json_file:

        if mode == 'r':

            # read metalist out of file
            info_metalist = json.load( json_file )

            output = info_metalist

        elif mode == 'w':

            # convert python metalist to JSON string
            output_JSON_str = json.dumps( output_py_metalist ) 

            json_file.write( output_JSON_str )
            
            output = True
    

    return output 




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def log_and_print( msg_format, log_type, logger ):

    getter = NL_TAB + "Getting "
    reader = NL_TAB + "Reading "
    writer = NL_TAB + "Writing "

    str_dict = {
            "COLLATE"       : NL_TAB + "collating lists...",
            "COMPLETE"      : " Complete! ",
            "F_COMMIT"      : NL_TAB + "filtering commits...",
            "F_MORE_COMMIT" : NL_TAB + "filtering commits...",
            "G_DATA_COMMIT" : getter + "commit data...",
            "G_DATA_ISSUE"  : getter + "issue data...",
            "G_DATA_PR"     : getter + "pull request data...",
            "G_MORE_COMMIT" : getter + "more commit data...",
            "G_MORE_ISSUE"  : getter + "more issue data...",
            "G_MORE_PAGES"  : getter + "more paginated lists...",
            "G_MORE_PR"     : getter + "more pull request data...",
            "G_PAGED_ISSUES": getter + "paginated list of issues...",
            "G_PAGED_PR"    : getter + "paginated list of pull requests...",
            "INVAL_TOKEN"   : """
    Invalid personal access token!
    Please see https://github.com/settings/tokens 
    to create a token with \"repo\" permissions!
""",
            "INVAL_ROW"     : NL_TAB + "row_quant config value is invalid!",
            "R_JSON_ALL"    : reader + "collated data JSON...",
            "R_JSON_COMMIT" : reader + "commit data JSON...",
            "R_JSON_ISSUE"  : reader + "issue data JSON...",
            "R_JSON_PR"     : reader + "pull request data JSON...",
            "SLEEP"         : NL_TAB + "Rate Limit imposed. Sleeping...",
            "V_ROW_#_ISSUE" : NL_TAB + "Validating row quantity config for issue data collection...",
            "V_ROW_#_PR"    : NL_TAB + "Validating row quantity config for pull request data collection...",
            "W_CSV_COMMIT"  : writer + "\"commit\" type CSV...",
            "W_CSV_PR"      : writer + "\"PR\" type CSV...",
            "W_JSON_ALL"    : writer + "master list of data to JSON...",
            "W_JSON_COMMIT" : writer + "list of commit data to JSON...",
            "W_JSON_ISSUE"  : writer + "list of issue data to JSON...",
            "W_JSON_PR"     : writer + "list of PR data to JSON...",
            "PROG_START"    : "\nAttempting program start...",
            }


    out_msg = str_dict[msg_format]

    if log_type == "INFO":
        logger.info( out_msg )

        if msg_format != "COMPLETE" and msg_format != "PROG_START":
            out_msg = INFO_MSG + out_msg

    elif log_type == "ERROR":
        logger.error( out_msg )
        out_msg = ERR_MSG + out_msg 

    elif log_type == "EXCEPT":
        logger.exception( out_msg )
        out_msg = EXCEPT_MSG + out_msg 
        

    if msg_format == "COMPLETE":
        out_msg = NL_TAB + TAB + BKGRN + out_msg + TXTRST + '\n'


    print( out_msg )



#--------------------------------------------------------------------------- 
# Function name: print_rem_calls 
# Process      : prints the amount of remaining calls that the
#                user-authenticated GitHub session has left for the current
#                hour. Acts as a wrapper for get_limit_info() with the
#                "remaining" flag.
# Parameters   : 
#                - name  : session
#                  - type: pygithub "Github" object
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library
#                  - docs: 
#                    - topic : pygithub Github objects 
#                      - link: https://pygithub.readthedocs.io/en/latest/github.html 
# Output       : prints remaining calls to screen during program execution
# Notes        : none
# Other Docs   : 
#                 - topic : str.format() method
#                   - link: https://www.w3schools.com/python/ref_string_format.asp
#--------------------------------------------------------------------------- 
def print_rem_calls( session ):

    # get remaining calls before reset
    remaining_calls = get_limit_info( session, "remaining" )

    # format as a string
    rem_calls_str = '{:<4d}'.format( remaining_calls ) 

    # clear line to erase any errors due to typing in the console
    print( "", end='\r' )

    # print output in place
    print( "        Calls left until sleep: " + rem_calls_str, end='\r' )

   


#--------------------------------------------------------------------------- 
# Function name: read_config
# Process      : opens and reads text file containing program configuration
#                info 
# Parameters   : 
#                 - name  : userinfo_file
#                   - type: .txt file
#                   - desc: contains GitHub user authentification info
#                   - docs: none
# Output       : 
#                 - name  : parsed_userinfo_list
#                   - type: list of str values
#                   - desc: contains the user auth info stripped of
#                           whitespace and new line chars
#                   - docs: none
# Notes        : none
# Other Docs   : none
#--------------------------------------------------------------------------- 
def read_config( config_file_name ):

    conf_list = []

    # append config file name for logging
    # first item in new list ( index 0 )
    conf_list.append( config_file_name ) 

    # read config file
    try:
        with open( config_file_name, 'r' ) as conffile_obj: 

            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            confinfo_list = [line.strip( '\n' ) for line in confinfo_list
                             if line[0] != '-' if line != '\n']

            for line in confinfo_list:
                
                stripped_line = line.replace( " ", '' )

                if stripped_line != '':

                    # split line at assignment operator
                    conf_sublist = stripped_line.split( "=" )

                    conf_line = conf_sublist[1]

                    conf_list.append( conf_line )

        # get auth_file name
        auth_file_name = conf_list[2]


    except FileNotFoundError:
        print( "\nConfiguration file not found!" ) 


    # read auth file
    else:
        try:
            with open( auth_file_name, 'r' ) as authfile_obj:

                # read contents out of auth file object
                # this should be one line with a personal accss token ( PAT )
                authinfo_line = authfile_obj.readline()

                # remove newline chars from PAT
                newLine_stripped_token = authinfo_line.strip( '\n' )
                    
                # remove leading and trailing whitespaces from PAT
                space_stripped_token = newLine_stripped_token.strip()

                # place PAT at end of list
                conf_list.append( space_stripped_token )

        except FileNotFoundError:
            print( "\nAuthorization file not found!" ) 
            

    # Total config length    : 15
    # list of config values ------
    #   config file name     : 0 
    #   repo name str        : 1
    #   row quant            : 3
    #   issue state          : 4
    #   pr state             : 5 
    #   diagnostics          : 6
    #   issue json filename  : 8
    #   pr json filename     : 9
    #   commit json filename : 10
    #   master json filename : 11
    #   pr csv filename      : 12
    #   commit csv filename  : 13
    #   session              : 14 

    if len( conf_list ) == 15:

        diagnostics_flag = conf_list[6] = str.lower( conf_list[6] )

        if diagnostics_flag == "true":
                
            print( NL + BKYEL + "[Diagnostics enabled]" + TXTRST )
            print( NL + DIAG_MSG + "Configuration is correct length!" )

        return conf_list

    else:
        print( "\nIncorrect configuration! Please update your settings!\n" )




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#---------------------------------------------------------------------------  
def read_json( file_name, msg_format, logger ):
    
    log_and_print( msg_format, "INFO", logger )
    info_list = json_io( file_name, 'r', None )
    complete( logger )  

    return info_list 




#--------------------------------------------------------------------------- 
# Function name: run_timer 
# Process      : acts as a wrapper for get_limit_info( "reset" ) and timer(),
#                calculating time until GitHub API calls can be made again and
#                sleeping the program run until then
# Parameters   : 
#
# Output       : program sleeps and prints remaining time
# Notes        : none
# Other Docs   : none
#--------------------------------------------------------------------------- 
def run_timer( session ):
    
    # get the amount of time until our call amount is reset
    sleep_time = get_limit_info( session, "reset" )

    # sleep for that amount of time
    timer( sleep_time ) 




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def sleep( session, msg_format, logger ):

    # sleep 
    log_and_print( "SLEEP", "EXCEPT", logger )
    run_timer( session ) 
    print() 

    # this allows us to choose to print a message after sleeping
    if msg_format is not None:
        log_and_print( msg_format, "INFO", logger )




#--------------------------------------------------------------------------- 
# Function name: timer
# Process      : convert seconds until permitted API call quantity restoration
#                into hours (will always be one) and sleep for that amount of
#                time, always decrementing by one second so as to print
#                countdown to screen
# Parameters   : 
#                - name  : session
#                  - type: pygithub "Github" object
#                  - desc: instance of "Github" class used to authenticate
#                          actions/calls to GitHub in pygithub library
#                  - docs: 
#                    - topic : pygithub Github objects 
#                      - link: https://pygithub.readthedocs.io/en/latest/github.html   
# Output       : program sleeps and prints remaining time 
# Notes        : implemented in run_timer() wrapper function
# Other Docs   : 
#                - topic : time library
#                  - link: https://docs.python.org/3/library/time.html
#                - topic : divmod
#                  - link: https://www.w3schools.com/python/ref_func_divmod.asp
#--------------------------------------------------------------------------- 
def timer( countdown_time ):

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




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def verify_dirs( file_path ):

    # init vars
    path_list_len = None


    # get only the last item in the file path, i.e. the item after the last
    # slash ( the file name )
    stripped_path_list = file_path.rsplit( '/', 1 )

    # the code below allows us to determine if the split performed above 
    # created two separate items. If not ( meaning the list length is 1 ),
    # only a file name was given and that file would be created in the same
    # directory as the extractor. If the length is greater than 1, 
    # we will have to either create or verify the existence of the path to the
    # file being created
    path_list_len = len( stripped_path_list )

    if path_list_len > 1:

        path = stripped_path_list[0]

        os.makedirs( path, exist_ok=True )




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def write_csv( master_info_list, out_file_name, output_type ):
    
    # init other vars

    list_index      = 0
    master_list_len = len( master_info_list ) 

    col_names   = ["Issue_Number", "Issue_Title", "Issue_Author_Name",      
                   "Issue_Author_Login","Issue_Closed_Date", "Issue_Body",  
                   "Issue_Comments", "PR_Title", "PR_Author_Name",          
                   "PR_Author_Login", "PR_Closed_Date", "PR_Body",          
                   "PR_Comments", "Commit_Author_Name",                     
                   "Commit_Date", "Commit_Message", "isPR"]                  

    if output_type == "commit":
        col_names = ["Author_Login", "Committer_Login", "PR_Number",
                     "SHA", "Commit_Message", "file_Name",
                     "Patch_Text", "Additions", "Deletions",
                     "Status", "Changes"] 

    
    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        # write column labels
        writer.writerow( col_names ) 

        # aggregate data lists into rows
        while list_index < master_list_len:

            pr_title        = NAN 
            pr_author_name  = NAN
            pr_author_login = NAN
            pr_closed_date  = NAN
            pr_body         = NAN
            pr_comments     = NAN  

            commit_author_name = NAN
            commit_message     = NAN
            commit_date        = NAN    
            commit_file_list   = NAN
            commit_patch_text  = NAN   


            # master JSON row order
            # ---------------------
            #
            #   issue info : 0-6
            #       issue_num         : 0
            #       issue_title_str   : 1
            #       issue_name_str    : 2
            #       issue_login_str   : 3
            #       issue_closed_date : 4
            #       issue_body_str    : 5
            #       issue_comment_str : 6
            #
            #   pr info    : [7][0-6] ( list of len == 7 at 7th index )
            #       pr_num          : 7[0]
            #       pr_title        : 7[1]
            #       pr_author_name  : 7[2]
            #       pr_author_login : 7[3]
            #       pr_closed_date  : 7[4]
            #       pr_body         : 7[5]
            #       pr_comments     : 7[6]
            #
            #   commit info: [8][0-10] ( list of len == 11 at 8th index )
            #       commit_author_name       : 8[0] 
            #       commit_message           : 8[1] 
            #       commit_date              : 8[2] 
            #       commit_committer         : 8[3] 
            #       commit_SHA               : 8[4] 
            #       commit_file_list         : 8[5] 
            #       commit_patch_text        : 8[6] 
            #       commit_adds              : 8[7] 
            #       commit_removes           : 8[8] 
            #       quoted_commit_status_str : 8[9] 
            #       commit_changes           : 8[10]
            #
            #   isPR       : -1 ( last position )

            cur_issue          = master_info_list[list_index]
            isPR               = cur_issue[-1]

            issue_num          = cur_issue[0]
            issue_title        = cur_issue[1]
            issue_author_name  = cur_issue[2]
            issue_author_login = cur_issue[3]
            issue_closed_date  = cur_issue[4] 
            issue_body         = cur_issue[5] 
            issue_comments     = cur_issue[6]   

            if isPR == 1:

                pr_title          = cur_issue[7][1] 
                pr_author_name    = cur_issue[7][2]
                pr_author_login   = cur_issue[7][3]
                pr_closed_date    = cur_issue[7][4]
                pr_body           = cur_issue[7][5]
                pr_comments       = cur_issue[7][6]  

                commit_author_name = cur_issue[8][0]
                commit_message     = cur_issue[8][1]
                commit_date        = cur_issue[8][2]   
                commit_file_list   = cur_issue[8][5]
                commit_patch_text  = cur_issue[8][6]  

           
            if output_type == "pr":
                
                # Output orders
                # ------------------------------------------------------------
                # our order: "Issue_Number", "Issue_Title", "Issue_Author_Name",
                #            "Issue_Author_Login","Issue_Closed_Date", "Issue_Body",
                #            "Issue_Comments", "PR_Title", "PR_Author_Name",
                #            "PR_Author_Login", "PR_Closed_Date", "PR_Body", 
                #            "PR_Comments", "Commit_Author_Name",
                #            "Commit_Date", "Commit_Message", "isPR"   
                # ------------------------------------------------------------
                # Daniels: issue_num, issue_closed_date, issue_author_login, 
                #          issue_title, issue_body, pr_closed_date, pr_title, 
                #          pr_comments, issue_comments,  pr_author_name, 
                #          commit_author_name, commit_date, commit_message, 
                #          isPR] 
                # ------------------------------------------------------------

                output_row = [issue_num, issue_title, issue_author_name,  
                              issue_author_login, issue_closed_date, issue_body,
                              issue_comments, pr_title, pr_author_name,
                              pr_author_login, pr_closed_date, pr_body, 
                              pr_comments, commit_author_name,
                              commit_date, commit_message, isPR]  


            elif output_type == "commit" and isPR == 1: 

                # order:  Author_Login, Committer_login, PR_Number,     
                #         SHA, Commit_Message, File_name,               
                #         Patch_text, Additions, Deletions,             
                #         Status, Changes                               
                # ------------------------------------------------------------
                # output_row = [commit_author_name, commit_committer, issue_num,
                #               commit_SHA, commit_message, commit_file_list,
                #               commit_patch_text, commit_adds, commit_rms,
                #               commit_status, commit_changes] 

                output_row = [ issue_num, issue_author_name, issue_title,
                               issue_body, commit_message, commit_file_list,
                               issue_closed_date, commit_patch_text ] 

                if len( commit_file_list ) > 0:
                    print( "\nPR num: " + issue_num + "; issue title: " + issue_title )
                    print( "commit message: " + commit_message )

                    print( commit_file_list )
                
                    writer.writerow( output_row ) 


            list_index += 1




#--------------------------------------------------------------------------- 
# Function name: write_issue_json
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def write_json( info_metalist, json_filename, msg_format, logger, ):

    log_and_print( msg_format, "INFO", logger )

    verify_dirs( json_filename )

    json_io( json_filename, 'w', info_metalist )

    complete( logger ) 




if __name__ == '__main__':
    main() 
 
