# ---------------------------------------------------------------------------
# Authors: Jacob Penney and Jacob Stuck
# Notes  : documentation for pygithub can be found @
#          https://pygithub.readthedocs.io/en/latest/index.html
# --------------------------------------------------------------------------- 


# TODO:

#   HIGH:   
#   0. Determine what the most important piece of data is, e.g.        
#      Do we only want to include data if the issue is related to a PR  
#   1. create checks to protect from lack of PRs and commits?
#   2. circumvent socket timeout
#       - where does it come from?

#   LOW:
#   - add ability to loop back into main from rate limit exception
#   - post-completion:
#       - clean annotations


# imports
import argparse
import csv
import github
import time


# constants
COMMIT_COL_NAMES = ["Author_Login", "Committer_login", "PR_Number",
                    "SHA", "Commit_Message", "File_name",
                    "Patch_text", "Additions", "Deletions",
                    "Status", "Changes"]

INVALID_TOKEN_STR = """\n    Invalid personal access token!\n 
    Please see https://github.com/settings/tokens 
    to create a token with \"repo\" permissions!""" 

PR_COL_NAMES  = ["PR_Number", "Issue_Closed_Date", "Issue_Author",
                 "Issue_Title", "Issue_Body", "PR_Closed_Date", 
                 "PR_Title", "PR_Body", "PR_Comments",
                 "Issue_Comments", "PR_Author", "Commit_Author", 
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
    conf_list = read_user_info( config_file_name ) 
    auth_token = conf_list[1]
        
    # authenticate the user with GitHub
    session = github.Github( auth_token ) 
    conf_list[1] = session

    try:
        # get value to test if user is properly authenticated
        session.get_user().name                                       


    except github.BadCredentialsException:
        print( INVALID_TOKEN_STR )

    except github.RateLimitExceededException:
        run_timer( session ) 
        exe_gather_and_write( conf_list )
        

    else:
        exe_gather_and_write( conf_list )

        


#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def exe_gather_and_write( conf_list ):

    output_type     = conf_list[0]
    session         = conf_list[1]
    repo_str        = conf_list[2]
    row_quant       = conf_list[3]
    out_file_name   = conf_list[4]
 
    
    print( "\nAttempting program start..." )

    # display remaining calls to GitHub
    print_rem_calls( session ) 
     
    # retrieve metalists of pull request, commit, and issue data
    metalist_list = get_info_metalists( session, repo_str, 
                                        row_quant, output_type )

    pr_info_list     = metalist_list[0]
    commit_info_list = metalist_list[1]

    # gather list lens and init issue_list_len to == pr_list_len
    #   this makes certain test passes if output_type is not "pr"
    pr_list_len     = len( pr_info_list ) 
    commit_list_len = len( commit_info_list )
    issue_list_len  = pr_list_len

    if output_type == "pr":
        issue_info_list = metalist_list[2]
        issue_list_len = len( issue_info_list )

    print()
    print( pr_list_len )
    print( commit_list_len )
    print( issue_list_len )


    # TODO:
    #   Determine what the most important piece of data is, e.g.
    #   Do we only want to include data if the issue is related to a PR 
    if pr_list_len == commit_list_len and pr_list_len == issue_list_len:
        row_quant = pr_list_len

        write_csv_output( metalist_list, row_quant, output_type, out_file_name )

    else:
        print( '\n' )
        print( "Info lists are incongruent length! See info getter functions!" )




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
def get_commit_info( session, commit_py_list, row_quant, output_type ):

    # commit list entry init
    #   This is necessary to prevent empty entries/indice misallignment 
    #   during data aggregation in write_csv_output if a commit does not
    #   exist 
    commit_author            = " =||= "
    commit_message           = " =||= "
    commit_date              = " =||= "
    commit_committer         = " =||= "
    commit_SHA               = " =||= "             
    commit_file_list         = " =||= "             
    commit_patch_text        = " =||= "     
    commit_adds              = " =||= "
    commit_removes           = " =||= "            
    quoted_commit_status_str = " =||= "
    commit_changes           = " =||= "         

    # establish entire list
    commit_info_list = [ commit_author, commit_message, commit_committer,
                         commit_SHA, commit_file_list, commit_patch_text,
                         commit_adds, commit_removes, quoted_commit_status_str,
                         commit_changes ] 

    # init other vars
    commit_file_list     = [] 
    commit_info_metalist = []
    commit_list_index    = 0
    cur_commit           = None

    # enforce index safety
    if row_quant == str.lower( "all" ):
        row_quant = len( commit_py_list )

    else:
        row_quant = int( row_quant )


    # begin process  
    print( "\n\nGetting commit info..." )

    while commit_list_index < row_quant:
        try:
            # retrieve list of commits for one pr
            cur_commit = commit_py_list[commit_list_index] 

            if cur_commit is not None:

                # get relevant author
                commit_author = cur_commit.commit.author.name

                # get relevant commit message
                commit_message = cur_commit.commit.message

                commit_info_list = [ 
                        commit_author, 
                        commit_message 
                        ]

                # get output type-dependent info. Appends start at index 2
                if output_type == "pr":

                    # get relevant commit date
                    commit_date_raw = cur_commit.commit.author.date
                    commit_date = commit_date_raw.strftime( TIME_FORM_STR )

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
            commit_info_metalist.append( commit_info_list )

            # print remaining calls per hour
            print_rem_calls( session )

            commit_list_index += 1


        except github.RateLimitExceededException:
            run_timer( session ) 


    return commit_info_metalist 




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def get_info_metalists( session, repo_str, row_quant, output_type ):
    
    # init vars
    metalist_list = []


    # get paginated lists of PRs and issues
    paged_list_tuple = get_paginated_lists( session, repo_str, output_type )

    pr_paged_list, issue_paged_list = paged_list_tuple


    # get metalist of pr information and commit info paginated list
    #   We get the commit paginated lists here because it allows us to segment
    #   each group of commits into their own lists. It is possible to retrieve
    #   a monolithic list of commits from the github object but they would not
    #   be broken up by PR
    pr_info_metalist, commits_paged_list = get_PR_info( session, pr_paged_list,
                                                        row_quant, output_type )
    

    # get metalist of commit information
    commit_info_metalist = get_commit_info( session, commits_paged_list,
                                            row_quant, output_type ) 


    # create list of metalists
    metalist_list = [ pr_info_metalist, commit_info_metalist ]
    

    # if creating PR file, retrieve issue metalist and update output
    if output_type == "pr":
        issue_info_metalist = get_issue_info( issue_paged_list, session,
                                              row_quant )

        metalist_list += [ issue_info_metalist ]


    return metalist_list


 

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
def get_issue_info( issue_paged_list, session, row_quant ):

    # init info entries that can be empty to prevent empty spaces in output
    issue_closed_date = " =||= "
    issue_comment_str = " =||= "

    # init vars 
    index             = 0
    isPR              = 0
    issue_info_list   = []
    issue_metalist    = []


    # enforce index safety
    if row_quant == str.lower( "all" ):
        row_quant = issue_paged_list.totalCount

    else:
        row_quant = int( row_quant ) 


    print( "\n\nGetting issue info..." )

    while index < row_quant:
        try:
            # work on one issue from paginated list at a time
            cur_issue         = issue_paged_list[index]          

            # get info from curret issue
            issue_author_str  = str( cur_issue.user.name ) 
            issue_body_str    = str( cur_issue.body )
            issue_title_str   = str( cur_issue.title )

            if cur_issue.closed_at is not None:
                issue_closed_date = str( cur_issue.closed_at.strftime( TIME_FORM_STR ))

            # get issue comment at last position
            comments_paged_list = cur_issue.get_comments() 

            # get comments if comments exist. Else, defaults to special char
            if comments_paged_list.totalCount > 0:
                last_comment_pos    = comments_paged_list.totalCount - 1
                last_comment        = comments_paged_list[last_comment_pos]
                issue_comment_str   = last_comment.body

            # check if the current issue has an associated PR
            if cur_issue.pull_request is not None:
                isPR = 1 
            
            if issue_author_str == "None":
                issue_author_str = " =||= "


            # clean and quote issue body str
            if issue_body_str == '':
                issue_body_str    = " =||= "

            else:
                issue_body_stripped = issue_body_str.strip( '\n' )
                issue_body_str      = issue_body_stripped 


            issue_info_list = [
                    issue_closed_date, 
                    issue_author_str, 
                    issue_title_str, 
                    issue_body_str,
                    issue_comment_str,
                    isPR
                    ]


            issue_metalist.append( issue_info_list )

            print_rem_calls( session )

            index += 1
        

        except github.RateLimitExceededException:
            run_timer( session )


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
def get_paginated_lists( session, repo_str, output_type ):

    # init vars 
    all_lists_retrieved = False
    issues_list         = []
    pr_list             = [] 

   
    # loop until both lists are fully retrieved
    while all_lists_retrieved == False:
        try:
            # retrieve GitHub repo object
            repo_obj = session.get_repo( repo_str )   

            # get base branch
            #   This precludes a bug where the repo returns no paginated lists
            base_branch = repo_obj.default_branch

            print( "\n\nGathering GitHub data paginated lists..." )
            
            # retrieve paginated list of pull requests
            pr_list = repo_obj.get_pulls( base="master", direction='asc', 
                                          sort='created', state='all' ) 

            if output_type == "pr": 
                # retrieve paginated list of issues
                issues_list = repo_obj.get_issues( direction='asc',
                                                   sort='created', 
                                                   state='closed' )


            print_rem_calls( session )

            all_lists_retrieved = True


        except github.RateLimitExceededException:
           run_timer( session ) 


    return pr_list, issues_list 




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
def get_PR_info( session, pr_paged_list, row_quant, output_type ):

    # init variables
    commits_list = []
    index        = 0
    pr_info_list = []
    pr_metalist  = []
        
    # establish base values
    most_recent_commit = " =||= "
    pr_author_str      = " =||= " 
    pr_closed_date_str = " =||= "
    pr_comment_str     = " =||= "
    pr_title_str       = " =||= "


    # enforce index safety
    if row_quant == str.lower( "all" ):
       row_quant = pr_paged_list.totalCount 

    else:
        row_quant = int( row_quant ) 


    print( "\n\nGetting pull request info..." )

    while index < row_quant:
        try:

            # get the current PR from the paginated list of PRs
            cur_pr     = pr_paged_list[index]
            
            # get the PR number
            pr_num_str = cur_pr.number

            # get paginated list of commits for each PR, to be processed
            # elsewhere
            pr_commits = cur_pr.get_commits()

            # each output type will require the pr num, so treat as default
            pr_info_list = [pr_num_str]  

            # add content based on output type
            if output_type == "pr":

                if cur_pr.closed_at is not None:
                    pr_closed_date_str = str( cur_pr.closed_at.strftime( TIME_FORM_STR )) 


                pr_author_str      = str( cur_pr.user.login ) 
                pr_body_str        = str( cur_pr.body )
                pr_comment_str     = str( cur_pr.comments )
                pr_title_str       = str( cur_pr.title )  

                #  clean each pr body of new line chars and place in quotes
                if pr_body_str == "":
                    pr_body_str = " =||= "

                else:
                    pr_body_str = pr_body_str.strip( '\n' )


                # add special string in place of empty comments
                if pr_comment_str == '0':
                    pr_comment_str = " =||= " 

                if pr_title_str == '':
                    pr_title_str = " =||= "


                pr_info_list += [
                        pr_author_str,
                        pr_body_str,
                        pr_closed_date_str,
                        pr_comment_str,
                        pr_title_str,
                        ]

            # append each list of pr info to a metalist
            pr_metalist.append( pr_info_list )

            # check for the existence of useful indices to test if 
            # a PR has commits
            last_commit_position = pr_commits.totalCount - 1
            
            # test if index value is valid
            if last_commit_position > -1:

                #  get most recent commit
                most_recent_commit = pr_commits[last_commit_position]


            # append most recent commit to list of commits
            commits_list.append( most_recent_commit )

            # display remaining calls
            print_rem_calls( session )

            index+=1


        except github.RateLimitExceededException:
            run_timer( session ) 


    return pr_metalist, commits_list




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
    print( "    calls left: " + str( rem_calls_str ), end="\r" )  

   


#--------------------------------------------------------------------------- 
# Function name: read_user_info
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
def read_user_info( config_file_name ):

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
            

    if len( conf_list ) == 5:
        return conf_list

    else:
        print( "\nIncorrect configuration! Please update your settings!" )




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

    # sleep for that amount of time
    timer( sleep_time ) 




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
        countdown = '{:02d}:{:02d}'.format( minutes, seconds )

        # print time string on the same line each decrement
        print( "    time until calls can be made: " + countdown, end="\r" )

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
def write_csv_output( metalist_list, row_quant, output_type, out_file_name ):

    # index for aggregation loop
    aggregation_index   = 0

    # data lists
    issue_info_metalist  = []
    output_row           = [] 
    pr_info_metalist     = metalist_list[0]  
    commit_info_metalist = metalist_list[1]

    # output columns
    label_cols = COMMIT_COL_NAMES
 
    # define output_type-dependent vars
    if output_type == "pr":
        label_cols = PR_COL_NAMES
        issue_info_metalist = metalist_list[2]


    # Open the output csv file in preparation for writing
    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        print( "\n\nWriting data..." )

        # write column labels
        writer.writerow( label_cols ) 

        # aggregate data lists into rows
        while aggregation_index < row_quant:

            # get shared values
            cur_commit     = commit_info_metalist[aggregation_index]
            commit_author  = cur_commit[0]
            commit_message = cur_commit[1] 

            cur_pr         = pr_info_metalist[aggregation_index]
            pr_num         = cur_pr[0] 


            # get output type-dependent values
            if output_type == "pr":
                commit_date       = cur_commit[2] 
                
                cur_issue         = issue_info_metalist[aggregation_index]
                issue_closed_date = cur_issue[0] 
                issue_author      = cur_issue[1]
                issue_title       = cur_issue[2]
                issue_body        = cur_issue[3] 
                issue_comments    = cur_issue[4]  
                isPR              = cur_issue[5] 

                pr_author         = cur_pr[1] 
                pr_body           = cur_pr[2] 
                pr_closed_date    = cur_pr[3] 
                pr_comments       = cur_pr[4] 
                pr_title          = cur_pr[5] 


                # order: PR_Number, Issue_Closed_Date, Issue_Author,  
                #        Issue_Title, Issue_Body, PR_Closed_Date,     
                #        RR_Title, PR_Body, PR_Comments               
                #        Issue_Comments, PR_Author, Commit_Author, 
                #        Commit_Date, Commit_Message, isPR            
                # ------------------------------------------------------------
                output_row = [pr_num, issue_closed_date, issue_author,  
                              issue_title, issue_body, pr_closed_date,   
                              pr_title, pr_body, pr_comments,            
                              issue_comments, pr_author, commit_author,  
                              commit_date, commit_message, isPR]


            else:
                commit_committer  = cur_commit[2]
                commit_SHA        = cur_commit[3]
                commit_file_list  = cur_commit[4]
                commit_patch_text = cur_commit[5] 
                commit_adds       = cur_commit[6]
                commit_rms        = cur_commit[7]
                commit_status     = cur_commit[8] 
                commit_changes    = cur_commit[9] 


                # order:  Author_Login, Committer_login, PR_Number,     
                #         SHA, Commit_Message, File_name,               
                #         Patch_text, Additions, Deletions,             
                #         Status, Changes                               
                # ------------------------------------------------------------
                output_row = [commit_author, commit_committer, pr_num,
                              commit_SHA, commit_message, commit_file_list,
                              commit_patch_text, commit_adds, commit_rms,
                              commit_status, commit_changes]


            writer.writerow( output_row ) 
                             
            aggregation_index += 1
     

    print( "\nOutput complete" )



if __name__ == '__main__':
    main() 
 
