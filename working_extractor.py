# ---------------------------------------------------------------------------
# Authors: Jacob Penney
# Notes  : documentation for pygithub can be found @
#          https://pygithub.readthedocs.io/en/latest/index.html
# --------------------------------------------------------------------------- 


# TODO:
# HIGH:
#   - add ability to write JSON as program executes
#       - fix JSON exe
#   - add logger
#  NOTE:
#   
#   

# - post-completion:
#     - clean:
#         - annotations
#         - spacing


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

COMMIT_MENU_PROMPT = """
Please choose type of operation:                                      
    [1] get pull request and commit JSON lists
    [4] compile pull request and commit JSON lists into CSV"""  

ERR104_MSG = """
    Error 104: Connection aborted by peer (GitHub)! 
    This error could have transpired for a variety of reasons.
    Dumping to JSON and retrying at same index in 10 seconds!"""

INVALID_TOKEN_STR = """
    Invalid personal access token!
    Please see https://github.com/settings/tokens 
    to create a token with \"repo\" permissions!""" 

LOG_FORMAT = "%(asctime)s: %(message)s"    

LOG_HEADER = """ 
    Config: 
        - %s
        - %s
        - %s
        - %s
        - %s 
        - %s
        - %s
        - %s
        - %s
        - %s
        - %s
        - %s
"""

NAN = "NaN"

NL_TAB = "\n    "

PROG_TITLE = """
GITHUB REPO EXTRACTOR
---------------------
"""

PR_MENU_PROMPT = """
Please choose type of operation:                                      
    [1] get issue JSON list
    [2] get pull request and commit JSON lists
    [3] get all three relevant lists
    [4] compile pull request, commit, and issue JSON lists into CSV""" 


PR_COL_NAMES  = ["Issue_Number", "Issue_Title", "Issue_Author_Name",
                 "Issue_Author_Login","Issue_Closed_Date", "Issue_Body", 
                 "Issue_Comments", "PR_Title", "PR_Author_Name",
                 "PR_Author_Login", "PR_Closed_Date", "PR_Body", 
                 "PR_Comments", "Commit_Author_Name",
                 "Commit_Date", "Commit_Message", "isPR"]

TIME_FORM_STR = "%m/%d/%y %I:%M:%S %p"




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
    auth_token = conf_list[1]
        
    # authenticate the user with GitHub
    session = github.Github( auth_token, timeout=100, retry=10 ) 
    conf_list[1] = session

    try:
        # get value to test if user is properly authenticated
        session.get_user().name                                       


    except github.BadCredentialsException:
        print( INVALID_TOKEN_STR )

    except github.RateLimitExceededException:
        run_timer( session ) 
        exe_menu( conf_list )
        

    else:
        exe_menu( conf_list )




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def check_row_quant_safety( paged_list, config_quant ):

    output_quant    = 0
    stripped_quant  = config_quant.strip()
    str_param_quant = str.lower( stripped_quant )
    
    if str_param_quant == "all" or int( config_quant ) > paged_list.totalCount:
       output_quant = int( paged_list.totalCount )

    elif int( config_quant ) <= paged_list.totalCount:
        output_quant = int( config_quant ) 

    else:
        print( "\nrow_quant config value is invalid!" )


    return output_quant


#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def exe_menu( conf_list ):

    # gather config values
    output_type          = conf_list[0]
    session              = conf_list[1]
    repo_str             = conf_list[2]
    branch_name          = conf_list[3]
    row_quant            = conf_list[4]
    issue_state          = conf_list[5]
    pr_state             = conf_list[6]
    log_file_name        = conf_list[7]
    issue_json_filename  = conf_list[8]
    pr_json_filename     = conf_list[9]
    commit_json_filename = conf_list[10]
    csv_filename         = conf_list[11]

    # init other vars
    menu          = PR_MENU_PROMPT

    if output_type == "commit":
        menu = COMMIT_MENU_PROMPT 


    # establish logging capabilities
    logger = init_logger( log_file_name ) 

    # print config to log file
    # logger.info( LOG_HEADER % ( conf_list ) )

    # print program info to STDOUT
    print( PROG_TITLE )

    print( menu )
        
    # get user choice of operation
    op_choice = input("\nExecute ")


    # enact menu choices
    #   The first three choices have a lot of overlap in functionality. This
    #   set of conditionals allow us to broadly catch those choices and not
    #   repeat code
    if op_choice == "1" or op_choice == "2" or op_choice == "3": 

        # logger.info( "Program Started." )
        print( "\n\nAttempting program start..." )

        # retrieve paginated lists of pull request, commit, and issue data
        paged_metalist = get_paginated_lists( session, repo_str, branch_name, 
                                              pr_state, issue_state, op_choice )

        # empty metalist
        issue_paged_list, pr_paged_list = paged_metalist 


        if op_choice == "1" or op_choice == "3": 
            get_issue_json( session, issue_paged_list, row_quant, logger, 
                            issue_json_filename )
         

        if op_choice == "2" or op_choice == "3":
            get_PR_commit_json( session, pr_paged_list, row_quant, output_type, 
                                logger, pr_json_filename, commit_json_filename ) 


    elif op_choice == "4": 

        # read metalists out of JSON storage
        pr_info_list     = json_io( pr_json_filename, 'r', None )
        commit_info_list = json_io( commit_json_filename, 'r',  None )

        info_metalist_list = [pr_info_list, commit_info_list]


        if output_type == "pr":
            issue_info_list = json_io( issue_json_filename, 'r', None )
            info_metalist_list += [issue_info_list]

        write_pr_csv( info_metalist_list, csv_filename )
        # write_csv_output( info_metalist_list, output_type, csv_filename )




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
def get_commit_info( session, commit_py_list, output_type, json_filename ):

    # commit list entry init
    #   This is necessary to prevent empty entries/indice misallignment 
    #   during data aggregation in write_csv_output if a commit does not
    #   exist 
    commit_author            = NAN
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

    # establish entire list
    commit_info_list = [ commit_author, commit_message, commit_committer,
                         commit_SHA, commit_file_list, commit_patch_text,
                         commit_adds, commit_removes, quoted_commit_status_str,
                         commit_changes ] 

    # init other vars
    commit_file_list  = [] 
    commit_metalist   = []
    commit_list_index = 0
    cur_commit        = None


    # begin process  
    print( "\n\n    Getting commit info..." )

    while commit_list_index < len( commit_py_list ):
        try:
            # retrieve list of commits for one pr
            cur_commit = commit_py_list[commit_list_index] 

            if cur_commit != NAN:

                # get relevant author
                commit_author         = cur_commit.commit.author
                commit_author_name    = commit_author.name

                # get relevant commit message
                commit_message = cur_commit.commit.message

                commit_info_list = [
                        commit_author_name, 
                        commit_message]

                # get output type-dependent info. Appends start at index 2
                if output_type == "pr":

                    # get relevant commit date
                    commit_date = commit_author.date.strftime( TIME_FORM_STR )

                    commit_info_list += [commit_date]

                else:
                    
                    # reset variables
                    commit_adds          = 0
                    commit_changes       = 0
                    commit_file_list     = []
                    commit_patch_text    = ""
                    commit_removes       = 0
                    commit_status_str    = ""
                    
                    
                    # get relevant commit file list
                    commit_files = cur_commit.files 

                    # get relevant committer
                    commit_committer = cur_commit.commit.committer.name 

                    # get relevant commit SHA
                    commit_SHA = cur_commit.sha

                    # retrieve each modified file and place in list
                    for file in commit_files:
                        commit_file_list.append( file.filename )
                        commit_adds       += int( file.additions )
                        commit_changes    += int( file.changes )
                        commit_patch_text += str( file.patch ) + ", "
                        commit_removes    += int( file.deletions )
                        commit_status_str += file.status + ", "

                    
                    quoted_commit_status_str = "\"" + commit_status_str + "\""

            commit_info_list += [
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

    # init info entries that can be empty to prevent empty spaces in output
    issue_closed_date = NAN
    issue_comment_str = ""

    # init vars 
    index           = 0
    issue_info_list = []
    issue_metalist  = []

    safe_quant = check_row_quant_safety( issue_paged_list, row_quant )

    logger.info( "Beginning issue info acquisition." )
    print( "\n    Getting issue info..." )

    while index < safe_quant:
        try:
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
                issue_closed_date = closed_date_obj.strftime( TIME_FORM_STR )


            # get issue comment at last position
            comments_paged_list = cur_issue.get_comments() 

            if comments_paged_list.totalCount == 0:
                issue_comment_str = NAN

            else:
                for comment in comments_paged_list:
                    issue_comment_str += comment.body + " =||= "


            if issue_name_str == "None":
                issue_name_str = NAN


            if issue_login_str == "None":
                issue_login_str = NAN


            # clean and quote issue body str
            if issue_body_str is None or issue_body_str == '':
                issue_body_str = NAN

            else:
                issue_body_str = issue_body_str.strip( '\n' )  


            # check if the current issue has an associated PR
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
def get_paginated_lists( session, repo_str, branch, pr_state, issue_state, 
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

            print( "\n    Gathering GitHub data paginated lists..." )
            
            if op_choice == "1" or op_choice == "3":
                 issues_list = repo_obj.get_issues( direction='asc',
                                                    sort='created', 
                                                    state=issue_state )


            if op_choice == "2" or op_choice == "3":

                # different branches have different outputs. If a run isn't
                # returning any paginated lists for a certain type of data, e.g.
                # issues, try looking at the branch names, e.g. "master" vs "main"
                if branch == "default":
                    branch = repo_obj.default_branch 


                pr_list = repo_obj.get_pulls( base=branch, direction='asc',     
                                              sort='created', state=pr_state )  


            output_list = [issues_list, pr_list]

            print_rem_calls( session )

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
def get_PR_commit_json( session, pr_paged_list, row_quant, output_type, logger,
                        pr_json_filename, commit_json_filename ):
    
    # get metalist of pr information and commit info paginated list
    #   We get the commit paginated lists here because it allows us to segment
    #   each group of commits into their own lists. It is possible to retrieve
    #   a monolithic list of commits from the github object but they would not
    #   be broken up by PR
    pr_info_metalist, commits_paged_list = get_PR_info( session, pr_paged_list,
                                                        row_quant, output_type,
                                                        pr_json_filename )

    # get metalist of commit information
    commit_info_metalist = get_commit_info( session, commits_paged_list,
                                            output_type, commit_json_filename ) 


    json_io( pr_json_filename, 'w', pr_info_metalist )
    json_io( commit_json_filename, 'w', commit_info_metalist ) 




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
def get_PR_info( session, pr_paged_list, row_quant, output_type, json_filename ):

    # init variables
    commits_list       = []
    index              = 0
    pr_info_list       = []
    pr_metalist        = []
        
    # establish base values
    most_recent_commit = NAN
    pr_title_str       = NAN
    pr_author_name     = NAN 
    pr_author_login    = NAN 
    pr_closed_date_str = NAN
    pr_body_str        = NAN
    pr_comment_str     = NAN


    safe_quant = check_row_quant_safety( pr_paged_list, row_quant )


    print( "\n    Getting pull request info..." )

    while index < safe_quant:
        try:

            # get the current PR from the paginated list of PRs
            cur_pr      = pr_paged_list[index]
            cur_pr_user = cur_pr.user
            
            # get the PR number
            pr_num_str = str( cur_pr.number )

            # get paginated list of commits for each PR, to be processed
            # elsewhere
            pr_commits = cur_pr.get_commits()

            # each output type will require the pr num, so treat as default
            pr_info_list = [pr_num_str]  

            # add content based on output type
            if output_type == "pr":

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
                   pr_closed_date_str = cur_pr.closed_at.strftime( TIME_FORM_STR )


                pr_info_list += [
                        pr_title_str,
                        pr_author_name,
                        pr_author_login,
                        pr_closed_date_str,
                        pr_body_str,
                        pr_comment_str
                        ]

            # append each list of pr info to a metalist
            pr_metalist.append( pr_info_list )

            # test if index value is valid
            if pr_commits.totalCount - 1 > -1:

                # check for the existence of useful indices to test if 
                # a PR has commits 
                last_commit_position = pr_commits.totalCount - 1

                #  get most recent commit
                most_recent_commit = pr_commits[last_commit_position]

            else:
                most_recent_commit = NAN


            # append most recent commit to list of commits
            commits_list.append( most_recent_commit )

            # display remaining calls
            print_rem_calls( session )

            index+=1


        except github.RateLimitExceededException:
            run_timer( session ) 
            print( "    Getting more pull request info..." )

        except ConnectionError:
            print( ERR104_MSG, end='\r' )
            json_io( json_filename, 'w', pr_metalist )
            time.sleep(10) 


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
    formatter = logging.Formatter( LOG_FORMAT )
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


    # read config file
    try:
        with open( config_file_name, 'r' ) as conffile_obj: 

            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            for line in confinfo_list:

                # remove newline chars from each item in list
                newLine_stripped_line = line.replace( ' ', '' )

                # remove leading and trailing whitespaces from user info
                space_stripped_line = newLine_stripped_line.strip( '\n' )

                # split line at assignment operator
                conf_sublist = space_stripped_line.split( "=" )

                conf_list.append( conf_sublist[1] )


        # remove empty entries
        conf_list = [item for item in conf_list if item != ''] 

        # get auth_file name
        auth_file_name = conf_list[1]
     

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
                conf_list[1] = space_stripped_token


        except FileNotFoundError:
            print( "\nAuthorization file not found!" ) 
            

    if len( conf_list ) == 12:
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
    print ( CLEAR_LINE )




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
# Function name: write_csv_output
# Process      : open output CSV using file name given as CLI arg, 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def write_csv_output( metalist_list, output_type, out_file_name ):

    # index for aggregation loop
    master_index   = 0
    pr_index       = 0

    # data lists
    issue_info_metalist  = []
    output_row           = [] 
    pr_info_metalist     = metalist_list[0]  
    commit_info_metalist = metalist_list[1]
    loop_len             = len( pr_info_metalist )

    # output columns
    label_cols = COMMIT_COL_NAMES
 
    # define output_type-dependent vars
    if output_type == "pr":
        issue_info_metalist = metalist_list[2]
        label_cols          = PR_COL_NAMES
        loop_len            = len( issue_info_metalist )


    print( str( len( issue_info_metalist ) ) )
    print( str( len( pr_info_metalist ) ) )
    print( str( len( commit_info_metalist ) ) )

    # Open the output csv file in preparation for writing
#     with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:
# 
#         # create writer object
#         writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
#                              quotechar='\"', escapechar='\\' )
#           
#         print( "\n\n    Writing data..." )
# 
# 
#         write_pr_csv( metalist_list, writer ):
# 
#         # write column labels
#         writer.writerow( label_cols ) 
# 
#         # aggregate data lists into rows
#         while master_index < loop_len:
# 
#             # get shared values
#             cur_pr         = pr_info_metalist[pr_index]
#             pr_num         = cur_pr[0]  
# 
#             cur_commit     = commit_info_metalist[master_index]
#             commit_author_name  = cur_commit[0]
#             commit_message      = cur_commit[1] 
# 
#             # get output type-dependent values
#             if output_type == "pr":
#                 cur_issue          = issue_info_metalist[master_index]
#                 issue_num          = cur_issue[0]
#                 issue_title        = cur_issue[1]
#                 issue_author_name  = cur_issue[2]
#                 issue_author_login = cur_issue[3]
#                 issue_closed_date  = cur_issue[4] 
#                 issue_body         = cur_issue[5] 
#                 issue_comments     = cur_issue[6]  
# 
# 
#                 print( "\nissue num: " + issue_num )
#                 print( "pr num   : " + pr_num )
# 
#                 if issue_num == pr_num:
#                     pr_title          = cur_pr[1] 
#                     pr_author_name    = cur_pr[2] 
#                     pr_author_login   = cur_pr[3] 
#                     pr_closed_date    = cur_pr[4] 
#                     pr_body           = cur_pr[5] 
#                     pr_comments       = cur_pr[6]  
# 
#                     commit_date       = cur_commit[2] 
# 
#                     pr_index += 1
# 
#                 else:
#                     pr_title          = NAN 
#                     pr_author_name    = NAN 
#                     pr_author_login   = NAN 
#                     pr_closed_date    = NAN 
#                     pr_body           = NAN 
#                     pr_comments       = NAN  
# 
# 
#                     commit_date       = cur_commit[2]  
# 
# 
#                 # order: "Issue_Number", "Issue_Title", "Issue_Author_Name",
#                 #        "Issue_Author_Login","Issue_Closed_Date", "Issue_Body",
#                 #        "Issue_Comments", "PR_Title", "PR_Author_Name",
#                 #        "PR_Author_Login", "PR_Closed_Date", "PR_Body", 
#                 #        "PR_Comments", "Commit_Author_Name",
#                 #        "Commit_Date", "Commit_Message", "isPR"   
#                 # ------------------------------------------------------------
#                 output_row = [issue_num, issue_title, issue_author_name,  
#                               issue_author_login, issue_closed_date, issue_body,
#                               issue_comments, pr_title, pr_author_name,
#                               pr_author_login, pr_closed_date, pr_body, 
#                               pr_comments, commit_author_name,
#                               commit_date, commit_message, isPR]
#  
# 
# 
#             else:
#                 commit_committer  = cur_commit[2]
#                 commit_SHA        = cur_commit[3]
#                 commit_file_list  = cur_commit[4]
#                 commit_patch_text = cur_commit[5] 
#                 commit_adds       = cur_commit[6]
#                 commit_rms        = cur_commit[7]
#                 commit_status     = cur_commit[8] 
#                 commit_changes    = cur_commit[9] 
# 
# 
#                 # order:  Author_Login, Committer_login, PR_Number,     
#                 #         SHA, Commit_Message, File_name,               
#                 #         Patch_text, Additions, Deletions,             
#                 #         Status, Changes                               
#                 # ------------------------------------------------------------
#                 output_row = [commit_author_name, commit_committer, pr_num,
#                               commit_SHA, commit_message, commit_file_list,
#                               commit_patch_text, commit_adds, commit_rms,
#                               commit_status, commit_changes]
# 
# 
#             writer.writerow( output_row ) 
#                              
#             master_index += 1
     

    print( "\nOutput complete" )




def write_pr_csv( metalist_list, out_file_name ):

    # unpack list of metalists
    pr_metalist     = metalist_list[0]
    commit_metalist = metalist_list[1]
    issue_metalist  = metalist_list[2]

    # init pr vals
    pr_title        = NAN
    pr_author_name  = NAN
    pr_author_login = NAN
    pr_closed_date  = NAN
    pr_body         = NAN
    pr_comments     = NAN
 
    # init other vars
    issue_index    = 0
    pr_index       = 0
    issue_list_len = len( issue_metalist )
    pr_list_len    = len( pr_metalist )



    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        print( "\n\n    Writing data..." ) 


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

            if str(issue_num) == str(pr_num):
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
                          issue_title, pr_closed_date, pr_title, pr_comments,
                          issue_comments,  pr_author_name, commit_author_name,
                          commit_date, commit_message, isPR]                 


            writer.writerow( Daniels ) 

            issue_index += 1





def write_commit_csv( metalist_list, writer_obj ):

    pr_info_metalist     = metalist_list[0]  
    commit_info_metalist = metalist_list[1] 
     
    # write column labels
    writer_obj.writerow( COMMIT_COL_NAMES ) 



if __name__ == '__main__':
    main() 
 
