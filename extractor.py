# ---------------------------------------------------------------------------
# Authors: Jacob Penney
# Notes  : documentation for pygithub can be found @
#          https://pygithub.readthedocs.io/en/latest/index.html
# --------------------------------------------------------------------------- 


# TODO:
#    HIGH:
#       FEAT:
#           - fix comment getters
#               - as of rn, comment getters concatenate before writing to JSON. 
#                 It would be better if they were just stored as a list and
#                 concatenated at CSV writing so that we could choose which
#                 comments to use
# 
#       - add dict function to contain long str constants

#    MED:
#       - add ability to write JSON as program executes
#           - requires functions to "save" corrupted data, e.g. get rest of
#             data if it fails at less than row_quant

#    LOW:
#       - modify logger when needed
#       - post-completion:
#           - clean:
#               - annotations
#               - spacing
#               - logging and printing
#                   - clean up the statements, e.g. always logger then print,
#                     use dict to store long str instead of constants, put
#                     prints and logs in proper places


# imports
import argparse
import csv
import github
import json
import logging
import time


# constants
CLEAR_LINE = "\033[A                                     \033[A"

COMMIT_COL_NAMES = ["Author_Login", "Committer_login", "PR_Number",
                    "SHA", "Commit_Message", "File_name",
                    "Patch_text", "Additions", "Deletions",
                    "Status", "Changes"]

END_PROG = """
    END OF PROGRAM RUN

------------------------------------------------------------------------------
"""

ERR104_MSG = """
    Error 104: Connection aborted by peer (GitHub)! 
    This error could have transpired for a variety of reasons.
    Dumping to JSON and retrying at same index in 10 seconds!"""

INVALID_TOKEN_STR = """
    Invalid personal access token!
    Please see https://github.com/settings/tokens 
    to create a token with \"repo\" permissions!""" 

LOG_FORMAT = "\n%(asctime)s: %(message)s"    

LOG_HEADER = """ 
    PROGRAM START
    -------------

    Config used: 
        - config file name : %s
        - repo             : %s
        - branch name      : %s
        - session          : %s
        - rows             : %s
        - issue state      : %s        
        - pr state         : %s          
        - log file         : %s        

        - issue json file  : %s
        - pr JSON file     : %s
        - commit JSON file : %s

        - "pr" CSV file    : %s       
        - "commit" CSV file: %s"""      

NAN = "NaN"

PROG_INTRO = """
GITHUB REPO EXTRACTOR
---------------------

Please choose type of operation:                                      
    [1] get issue JSON list
    [2] get pull request and commit JSON lists
    [3] get all three relevant lists
    [4] compile JSON lists into CSV"""  

CSV_PROMPT = """
Please choose type of CSV:                                      
    [1] Pull Request
    [2] Commit
    [3] Both"""  


PR_COL_NAMES  = ["Issue_Number", "Issue_Title", "Issue_Author_Name",
                 "Issue_Author_Login","Issue_Closed_Date", "Issue_Body", 
                 "Issue_Comments", "PR_Title", "PR_Author_Name",
                 "PR_Author_Login", "PR_Closed_Date", "PR_Body", 
                 "PR_Comments", "Commit_Author_Name",
                 "Commit_Date", "Commit_Message", "isPR"]

TIME_FORMAT = "%m/%d/%y, %I:%M:%S %p"




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
    
    # retrieve positional arguments as variables
    config_file_name = get_CLI_args()

    # get prog run info
    conf_list = read_config( config_file_name ) 

    # establish logging capabilities
    log_filename = conf_list[7]
    logger       = init_logger( log_filename )  

    # authenticate the user with GitHub and insert session into list
    auth_token   = conf_list[3]
    session      = github.Github( auth_token, timeout=100, retry=10 ) 
    conf_list[3] = session

    try:
        # get value to test if user is properly authenticated
        session.get_user().name                                       


    except github.BadCredentialsException:
        print( INVALID_TOKEN_STR )

    except github.RateLimitExceededException:
        run_timer( session ) 
        exe_menu( conf_list, logger )
        

    else:
        try:
            exe_menu( conf_list, logger )


        except:
            logger.exception( "\n    Uncaught exception:\n\n" )
            print( "\n    Uncaught exception! Please see log file!" )


    finally:
        logger.info( END_PROG ) 




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def check_row_quant_safety( paged_list, config_quant, logger ):

    # init vars
    output_quant    = 0
    stripped_quant  = config_quant.strip()
    str_param_quant = str.lower( stripped_quant )
    

    # if all rows are desired or the desired amount is more than exist
    if str_param_quant == "all" or int( config_quant ) > paged_list.totalCount:
       output_quant = int( paged_list.totalCount )

    elif int( config_quant ) <= paged_list.totalCount:
        output_quant = int( config_quant ) 

    else:
        logger.error( "\n    row_quant config value is invalid." )
        print( "\n    row_quant config value is invalid!" )


    return output_quant




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
    branch_name          = conf_list[2]
    session              = conf_list[3]
    row_quant            = conf_list[4]
    issue_state          = conf_list[5]
    pr_state             = conf_list[6] 

    issue_json_filename  = conf_list[8]
    pr_json_filename     = conf_list[9]
    commit_json_filename = conf_list[10]

    pr_csv_filename      = conf_list[11]
    commit_csv_filename  = conf_list[12]

    # init other vars
    conf_tuple = tuple( conf_list )


    # print config to log file
    logger.info( LOG_HEADER %( conf_tuple ))

    try:

        print( PROG_INTRO )

        op_choice = input("\nExecute ")


        # exe menu choices
        #   The first three choices have a lot of overlap in functionality. This
        #   set of conditionals allow us to broadly catch those choices and not
        #   repeat code
        if op_choice == "1" or op_choice == "2" or op_choice == "3": 
        
            print( "\n\nAttempting program start..." )

            print_rem_calls( session )
            print()

            # retrieve paginated lists of pull request, commit, and issue data
            paged_metalist = get_paginated_lists( session, repo_str, branch_name,
                                                  logger, pr_state, issue_state,
                                                  op_choice )

            # empty metalist
            issue_paged_list, pr_paged_list = paged_metalist 


            if op_choice == "1" or op_choice == "3": 
                get_issue_json( session, issue_paged_list, row_quant, logger, 
                                issue_json_filename )
             

            if op_choice == "2" or op_choice == "3":

                get_PR_commit_json( session, pr_paged_list, row_quant, 
                                    logger, pr_json_filename, 
                                    commit_json_filename )


        elif op_choice == "4": 

            print( CSV_PROMPT )
            
            csv_choice = input("\nExecute ")

            print( "\n\nAttempting program start..." )

            # read metalists out of JSON storage
            #   the pr and commit lists are needed for both outputs
            logger.info( "\n    Reading pull request JSON." )
            print( "\n    Reading pull request JSON"  )
            pr_info_list     = json_io( pr_json_filename, 'r', None )

            logger.info( "\n    Reading commit JSON." )
            print( "\n    Reading commit JSON"  )
            commit_info_list = json_io( commit_json_filename, 'r',  None )

            info_metalist_list = [pr_info_list, commit_info_list]

            if csv_choice == "1" or csv_choice == "3":
                logger.info( "\n    Reading issue JSON." )
                print( "\n    Reading issue JSON"  )
                issue_info_list = json_io( issue_json_filename, 'r', None )

                info_metalist_list += [issue_info_list]

                logger.info( "\n    Writing \"pr\" type CSV." )
                print( "\n    Writing \"pr\" type CSV"  )
                write_pr_csv( info_metalist_list, pr_csv_filename )


            if csv_choice == "2" or csv_choice == "3":
                logger.info( "\n    Writing \"commit\" type CSV." )
                print( "\n    Writing \"commit\" type CSV"  )
                write_commit_csv( info_metalist_list, commit_csv_filename )


    except KeyboardInterrupt:
        logger.exception( "\n   Program interrupted by KeyboardInterrupt!\n\n" )
        print()




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
    config_file = arg_parser.parse_args().config_file


    return config_file




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
def get_commit_info( session, commit_py_list, logger, json_filename ):

    # init other vars
    commit_file_list  = [] 
    commit_metalist   = []
    commit_list_index = 0
    cur_commit        = None


    logger.info( "\n    Acquiring commit data." )
    print( "\n\n    Getting commit info..." ) 

    while commit_list_index < len( commit_py_list ):
        try:
             
            # reset variables
            commit_adds          = 0
            commit_changes       = 0
            commit_file_list     = []
            commit_patch_text    = ""
            commit_removes       = 0
            commit_status_str    = "" 

            # retrieve list of commits for one pr
            cur_commit = commit_py_list[commit_list_index] 

            if cur_commit != NAN:
                commit_author      = cur_commit.commit.author
                commit_author_name = commit_author.name
                commit_message     = cur_commit.commit.message
                commit_date        = commit_author.date.strftime( TIME_FORMAT )
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

            else:
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

            commit_list_index += 1


        except github.RateLimitExceededException:
            run_timer( session ) 
            print( "\n    Getting more commit info..." )

        except ConnectionError:
            print( ERR104_MSG )
            json_io( json_filename, 'w', commit_metalist )
            time.sleep(10) 


    print()

    return commit_metalist




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
def get_issue_info( session, issue_paged_list, row_quant, logger, json_filename ):
    
    # init vars 
    index           = 0
    issue_info_list = []
    issue_metalist  = []


    safe_quant = check_row_quant_safety( issue_paged_list, row_quant, logger )

    logger.info( "\n    Acquiring pull request data." )
    print( "\n    Getting issue info..." )  

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
                issue_closed_date = closed_date_obj.strftime( TIME_FORMAT )
            
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

            issue_metalist.append( issue_info_list )

            print_rem_calls( session )

            index += 1
        

        except github.RateLimitExceededException:
            logger.exception( "Rate Limit imposed. Sleeping." )
            run_timer( session )
            print( "\n    Getting more issue info..." )

        except ConnectionError:
            logger.exception( "Error 104. Sleeping." )
            print( ERR104_MSG )
            json_io( json_filename, 'w', issue_metalist )
            time.sleep(10)


    print()

    return issue_metalist




#--------------------------------------------------------------------------- 
# Function name: get_issue_json
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def get_issue_json( session, issue_paged_list, row_quant, logger, 
                    issue_json_filename ):


    issue_metalist = get_issue_info( session, issue_paged_list, row_quant,
                                     logger, issue_json_filename )

    logger.info( "\n    Writing issue data to JSON." )
    json_io( issue_json_filename, 'w', issue_metalist )




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
def get_paginated_lists( session, repo_str, branch, logger, pr_state, 
                         issue_state, op_choice ):

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
                
                logger.info( "\n    Acquiring paginated list of issues." )
                print( "\n    Gathering paginated list of issues..." )


                issues_list = repo_obj.get_issues( direction='asc',
                                                    sort='created', 
                                                    state=issue_state )

                print_rem_calls( session )
                print()


            if op_choice == "2" or op_choice == "3":

                # different branches have different outputs. If a run isn't
                # returning any paginated lists for a certain type of data, e.g.
                # issues, try looking at the branch names, e.g. "master" vs "main"
                if branch == "default":
                    branch = repo_obj.default_branch 


                logger.info( "\n    Acquiring paginated list of pull requests." )
                print( "\n    Gathering paginated list of pull requests..." )

                pr_list = repo_obj.get_pulls( base=branch, direction='asc',     
                                              sort='created', state=pr_state )  

                print_rem_calls( session )


            output_list = [issues_list, pr_list]

            all_lists_retrieved = True


        except github.RateLimitExceededException:
           run_timer( session ) 


    print()

    return output_list 




#--------------------------------------------------------------------------- 
# Function name: get_PR_commit_json
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def get_PR_commit_json( session, pr_paged_list, row_quant, logger, 
                        pr_json_filename, commit_json_filename ):
    
    # get metalist of pr information and commit info paginated list
    #   We get the commit paginated lists here because it allows us to segment
    #   each group of commits into their own lists. It is possible to retrieve
    #   a monolithic list of commits from the github object but they would not
    #   be broken up by PR
    pr_info_metalist, commits_paged_list = get_PR_info( session, pr_paged_list,
                                                        row_quant, logger )
    
    logger.info( "\n    Writing pull request data to JSON." )
    json_io( pr_json_filename, 'w', pr_info_metalist )
    logger.info( "\n    Finished writing pull request data to JSON." ) 
    

    commit_info_metalist = get_commit_info( session, commits_paged_list,
                                            logger, commit_json_filename ) 

    logger.info( "\n    Writing commit data to JSON." )
    json_io( commit_json_filename, 'w', commit_info_metalist ) 
    logger.info( "\n    Finished writing commit data to JSON." )




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
def get_PR_info( session, pr_paged_list, row_quant, logger ):

    # init variables
    commits_list       = []
    index              = 0
    pr_metalist        = []
        
    # establish base values
    most_recent_commit = NAN
    pr_title_str       = NAN
    pr_author_name     = NAN 
    pr_author_login    = NAN 
    pr_closed_date_str = NAN
    pr_body_str        = NAN
    pr_comment_str     = NAN


    safe_quant = check_row_quant_safety( pr_paged_list, row_quant, logger )

    logger.info( "\n    Acquiring pull request data and paginated list of commits." )
    print( "\n    Getting pull request info..." ) 

    while index < safe_quant:
        try:
            # get the current PR from the paginated list of PRs
            cur_pr      = pr_paged_list[index]
            cur_pr_user = cur_pr.user
            
            # get the PR number
            pr_num_str      = str( cur_pr.number )
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
               pr_closed_date_str = cur_pr.closed_at.strftime( TIME_FORMAT )


            pr_info_list = [
                    pr_num_str,
                    pr_title_str,
                    pr_author_name,
                    pr_author_login,
                    pr_closed_date_str,
                    pr_body_str,
                    pr_comment_str
                    ]

            # get paginated list of commits for each PR, to be processed
            # elsewhere
            pr_commits = cur_pr.get_commits() 

            print( "\nPR num:" + pr_num_str )
            print( "PR_commits totalCount:" + str( pr_commits.totalCount ) )  

            # test if index value is valid
            if pr_commits.totalCount > 0:

                # check for the existence of useful indices to test if 
                # a PR has commits 
                last_commit_position = pr_commits.totalCount - 1

                #  get most recent commit
                most_recent_commit = pr_commits[last_commit_position]

            else:
                most_recent_commit = NAN
                print( "most_recent_commit == NAN" ) 


        except github.RateLimitExceededException:
            run_timer( session ) 

        except ConnectionError:
            print( ERR104_MSG, end='\r' )
            time.sleep(10) 


        else:
            # append each list of pr info to a metalist
            pr_metalist.append( pr_info_list ) 

            # append most recent commit to list of commits
            commits_list.append( most_recent_commit ) 

            # display remaining calls
            print_rem_calls( session )

            print( "\nlen of pr list     : " + str( len( pr_metalist ) ) )
            print( "len of commits list: " + str( len( commits_list ) ) ) 

            index += 1 


    return pr_metalist, commits_list
 



#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def init_logger( log_file_name ):

    # create logger
    logger = logging.getLogger( __name__ )

    # create file handling
    out_file_handler = logging.FileHandler( log_file_name )

    # create formatting
    formatter = logging.Formatter( LOG_FORMAT, TIME_FORMAT )
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
def json_io( file_name, mode, output_py_metalist ):

    output = True

    # write JSON string to file
    with open( file_name, mode ) as json_file:

        if mode == 'r':

            # read metalist out of file
            info_metalist = json.load( json_file )

            output = info_metalist

        elif mode == 'w':

            # convert python metalist to JSON string
            output_JSON_str = json.dumps( output_py_metalist ) 

            json_file.write( output_JSON_str )
    

    return output 




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
    rem_calls_str = '{:4d}'.format( remaining_calls ) 

    # print output in place
    print( "        calls left until sleep: " + str( rem_calls_str ), end='\r' )

   


#--------------------------------------------------------------------------- 
# Function name: read_config
# Process      : opens and reads text file containing GitHub user
#                authentification info in the format:
#                       
#                       <username>
#                       <personal access token>
#
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
    conf_list.append( config_file_name ) 

    # read config file
    try:
        with open( config_file_name, 'r' ) as conffile_obj: 

            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            for line in confinfo_list:

                # remove newline chars from each item in list
                nl_stripped_line = line.strip( '\n' ) 

                if nl_stripped_line != '':

                    # remove whitespaces from user info
                    space_stripped_line = nl_stripped_line.replace( ' ', '' )

                    # do not parse empty lines or ones that start with a dash
                    #   this allows us to use a dash to begin a comment in the
                    #   config file
                    if space_stripped_line[0] != "-":

                        # split line at assignment operator
                        conf_sublist = space_stripped_line.split( "=" )
                    
                        conf_list.append( conf_sublist[1] )


        # get auth_file name
        auth_file_name = conf_list[3]


    except FileNotFoundError:
        print( "\nConfiguration file not found!" ) 


    # read auth file
    else:
        try:
            with open( auth_file_name, 'r' ) as authfile_obj:

                # read contents out of file object
                authinfo_line = authfile_obj.readline()

                # remove newline chars from each item in list
                newLine_stripped_token = authinfo_line.strip( '\n' )
                    
                # remove leading and trailing whitespaces from user info
                space_stripped_token = newLine_stripped_token.strip()

                # place each item into a new list if it has content
                conf_list[3] = space_stripped_token


        except FileNotFoundError:
            print( "\nAuthorization file not found!" ) 
            

    if len( conf_list ) == 13:
        return conf_list

    else:
        print( "\nIncorrect configuration! Please update your settings!\n" )




#--------------------------------------------------------------------------- 
# Function name: run_timer 
# Process      : acts as a wrapper for get_limit_info( "reset" ) and timer(),
#                calculating time until GitHub API calls can be made again and
#                sleeping the program run until then
# Parameters   : 

# Output       : program sleeps and prints remaining time
# Notes        : none
# Other Docs   : none
#--------------------------------------------------------------------------- 
def run_timer( session ):
    
    # get the amount of time until our call amount is reset
    sleep_time = get_limit_info( session, "reset" )

    print( "\n\n    Sleeping..." )

    # sleep for that amount of time
    timer( sleep_time ) 

    # clear preceding line
    print ( CLEAR_LINE + CLEAR_LINE )




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
def write_pr_csv( metalist_list, out_file_name ):

    # unpack list of metalists
    pr_metalist     = metalist_list[0]
    commit_metalist = metalist_list[1]
    issue_metalist  = metalist_list[2]

    # init other vars
    issue_index    = 0
    pr_index       = 0
    issue_list_len = len( issue_metalist )


    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        # write column labels
        writer.writerow( PR_COL_NAMES )

        while issue_index < issue_list_len:

            # reset vars
            pr_title        = NAN
            pr_author_name  = NAN
            pr_author_login = NAN
            pr_closed_date  = NAN
            pr_body         = NAN
            pr_comments     = NAN 
            isPR = 0

            commit_author_name = NAN
            commit_message     = NAN
            commit_date        = NAN  
            
            # get issue info 
            cur_issue          = issue_metalist[issue_index]
            issue_num          = cur_issue[0]
            issue_title        = cur_issue[1]
            issue_author_name  = cur_issue[2]
            issue_author_login = cur_issue[3]
            issue_closed_date  = cur_issue[4] 
            issue_body         = cur_issue[5] 
            issue_comments     = cur_issue[6]  

            # get PR info
            cur_pr = pr_metalist[pr_index] 
            pr_num = cur_pr[0]                  

            if issue_num == pr_num:

                isPR = 1

                pr_title          = cur_pr[1] 
                pr_author_name    = cur_pr[2] 
                pr_author_login   = cur_pr[3] 
                pr_closed_date    = cur_pr[4] 
                pr_body           = cur_pr[5] 
                pr_comments       = cur_pr[6]   

                cur_commit         = commit_metalist[pr_index]
                commit_author_name = cur_commit[0]
                commit_message     = cur_commit[1]
                commit_date        = cur_commit[2]  

                pr_index += 1


            # order: "Issue_Number", "Issue_Title", "Issue_Author_Name",
            #        "Issue_Author_Login","Issue_Closed_Date", "Issue_Body",
            #        "Issue_Comments", "PR_Title", "PR_Author_Name",
            #        "PR_Author_Login", "PR_Closed_Date", "PR_Body", 
            #        "PR_Comments", "Commit_Author_Name",
            #        "Commit_Date", "Commit_Message", "isPR"   
            # ------------------------------------------------------------

            # output_row = [issue_num, issue_title, issue_author_name,  
            #               issue_author_login, issue_closed_date, issue_body,
            #               issue_comments, pr_title, pr_author_name,
            #               pr_author_login, pr_closed_date, pr_body, 
            #               pr_comments, commit_author_name,
            #               commit_date, commit_message, isPR] 

            Daniels    = [issue_num, issue_closed_date, issue_author_login, 
                          issue_title, issue_body, pr_closed_date, pr_title, 
                          pr_comments, issue_comments,  pr_author_name, 
                          commit_author_name, commit_date, commit_message, 
                          isPR]


            writer.writerow( Daniels ) 

            issue_index += 1


    print( "\n    CSV Output complete" )




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def write_commit_csv( metalist_list, out_file_name ):
    
    # unpack list of metalists
    pr_metalist     = metalist_list[0]
    commit_metalist = metalist_list[1]

    print( "\nPR list len: " + str( len( pr_metalist )))
    print( "Commit list len: " + str( len( commit_metalist )))

    # init other vars
    index       = 0
    pr_list_len = len( pr_metalist )

    
    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        # write column labels
        writer.writerow( COMMIT_COL_NAMES ) 

        # aggregate data lists into rows
        while index < pr_list_len:

            cur_pr              = pr_metalist[index]
            pr_num              = cur_pr[0]  

            cur_commit          = commit_metalist[index]
            commit_author_name  = cur_commit[0]
            commit_message      = cur_commit[1] 
            commit_committer    = cur_commit[3]
            commit_SHA          = cur_commit[4]
            commit_file_list    = cur_commit[5]
            commit_patch_text   = cur_commit[6] 
            commit_adds         = cur_commit[7]
            commit_rms          = cur_commit[8]
            commit_status       = cur_commit[9] 
            commit_changes      = cur_commit[10] 


            # order:  Author_Login, Committer_login, PR_Number,     
            #         SHA, Commit_Message, File_name,               
            #         Patch_text, Additions, Deletions,             
            #         Status, Changes                               
            # ------------------------------------------------------------
            output_row = [commit_author_name, commit_committer, pr_num,
                          commit_SHA, commit_message, commit_file_list,
                          commit_patch_text, commit_adds, commit_rms,
                          commit_status, commit_changes]


            writer.writerow( output_row ) 
                             
            index += 1
 

    print( "\n    CSV Output complete" )




if __name__ == '__main__':
    main() 
 
