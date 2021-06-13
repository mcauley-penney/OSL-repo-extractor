#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 


from . import cfg
from . import log_ops
from . timer_ops import print_rem_calls, sleep
import github


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
    

    # if all rows are desired or the desired amount is more than exists, adjust
    if str_param_quant == "all" or int( config_quant ) > paged_list.totalCount:
       output_quant = int( paged_list.totalCount )

    elif int( config_quant ) <= paged_list.totalCount:
        output_quant = int( config_quant ) 

    else:
        log_ops.log_and_print( "INVAL_ROW", "ERROR", logger )


    return output_quant  




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
def get_commit_info( session, commit_py_list, logger ):

    # init other vars
    commit_file_list  = [] 
    commit_metalist   = []
    commit_list_index = 0
    cur_commit        = None

    
    log_ops.log_and_print( "G_DATA_COMMIT", "INFO", logger )

    while commit_list_index < len( commit_py_list ):
        try:
             
            # reset variables
            commit_author_name       = cfg.NAN
            commit_message           = cfg.NAN
            commit_date              = cfg.NAN
            commit_committer         = cfg.NAN
            commit_SHA               = cfg.NAN
            commit_file_list         = cfg.NAN
            commit_patch_text        = cfg.NAN
            commit_adds              = cfg.NAN
            commit_removes           = cfg.NAN
            quoted_commit_status_str = cfg.NAN
            commit_changes           = cfg.NAN 

            commit_adds          = 0
            commit_changes       = 0
            commit_file_list     = []
            commit_patch_text    = ""
            commit_removes       = 0
            commit_status_str    = "" 

            # retrieve list of commits for one pr
            cur_commit = commit_py_list[commit_list_index] 

            if cur_commit != cfg.NAN:

                commit_author      = cur_commit.commit.author
                commit_author_name = commit_author.name
                commit_message     = cur_commit.commit.message
                commit_date        = commit_author.date.strftime( cfg.TIME_FRMT )
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

            commit_list_index += 1


        except github.RateLimitExceededException:
            print()
            sleep( session, "G_DATA_COMMIT", logger )


    log_ops.complete( logger )

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
def get_issue_info( session, issue_paged_list, row_quant, diagnostics, logger ):
    
    # init vars 
    index           = 0
    issue_info_list = []
    issue_metalist  = []


    safe_quant = check_row_quant_safety( issue_paged_list, row_quant, logger )

    log_ops.log_and_print( "G_DATA_ISSUE", "INFO", logger )

    if diagnostics == "true":
        print( cfg.NL_TAB + cfg.DIAG_MSG )


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
                issue_closed_date = closed_date_obj.strftime( cfg.TIME_FRMT )
            
            else:
                issue_closed_date = cfg.NAN


            # get issue comment at last position
            comments_paged_list = cur_issue.get_comments() 

            
            if comments_paged_list.totalCount == 0:
                issue_comment_str = cfg.NAN

            else:
                for comment in comments_paged_list:
                    issue_comment_str += comment.body + " =||= "


            if issue_name_str == "":
                issue_name_str = cfg.NAN


            if issue_login_str == "":
                issue_login_str = cfg.NAN


            if issue_body_str is None or issue_body_str == "":
                issue_body_str = cfg.NAN

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


    log_ops.complete( logger )

    return issue_metalist
 



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
                
                log_ops.log_and_print( "G_PAGED_ISSUES", "INFO", logger )

                issues_list = repo_obj.get_issues( direction='asc',
                                                    sort='created', 
                                                    state=issue_state )

                print_rem_calls( session )

                log_ops.complete( logger )


            if op_choice == "2" or op_choice == "3":

                log_ops.log_and_print( "G_PAGED_PR", "INFO", logger )
                
                pr_list = repo_obj.get_pulls( direction='asc',
                                              sort='created', state=pr_state )  

                print_rem_calls( session )

                log_ops.complete( logger )


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
    commits_list       = []
    index              = 0
    pr_metalist        = []

    # diagnostics strings
    commit_list_len_diag = "        Length of commits list: "
    commits_per_pr_diag  = "        Number of commits/pr  : " 
    pr_list_len_diag     = "        Length of pr lists    : " 
    pr_num_diag          = "\n\n        PR num                : "


    safe_quant = check_row_quant_safety( pr_paged_list, row_quant, logger )

    log_ops.log_and_print( "G_DATA_PR", "INFO", logger )

    if diagnostics == "true":
        print( cfg.NL_TAB + cfg.DIAG_MSG )


    while index < safe_quant:

        # reset vars
        most_recent_commit = cfg.NAN
        pr_title_str       = cfg.NAN
        pr_author_name     = cfg.NAN 
        pr_author_login    = cfg.NAN 
        pr_closed_date_str = cfg.NAN
        pr_body_str        = cfg.NAN
        pr_comment_str     = cfg.NAN 

        cur_pr = pr_paged_list[index]

        try:
            if cur_pr.merged == True:
                try:
                    cur_pr_user = cur_pr.user
                    
                    pr_num_str      = str( cur_pr.number )

                    pr_title_str    = cur_pr.title
                    pr_author_name  = cur_pr_user.name
                    pr_author_login = cur_pr_user.login
                    pr_body_str     = cur_pr.body 

                    if pr_title_str == "":
                        pr_title_str = cfg.NAN 


                    #  clean each pr body of new line chars and place in quotes
                    if pr_body_str is None or pr_body_str == "":
                        pr_body_str = cfg.NAN

                    else:
                        pr_body_str = pr_body_str.strip( '\n' )


                    if cur_pr.closed_at is not None:
                       pr_closed_date_str = cur_pr.closed_at.strftime( cfg.TIME_FRMT )


                    pr_info_list = [
                            pr_num_str,
                            pr_title_str,
                            pr_author_name,
                            pr_author_login,
                            pr_closed_date_str,
                            pr_body_str,
                            pr_comment_str
                            ]

                    # get paginated list of commits for each PR
                    cur_pr_commits = cur_pr.get_commits() 
                    num_of_commits = cur_pr_commits.totalCount

                    # test if this PR has commits
                    # if not, we do not want to include it
                    if num_of_commits > 0:

                        # get index of last commit
                        last_commit_position = num_of_commits - 1

                        # store last/most recent commit
                        commit_of_interest = cur_pr_commits[last_commit_position]

                        # check if the commit has changed files and omit if not
                        commit_files        = commit_of_interest.files
                        num_of_commit_files = len( commit_files ) 

                        if num_of_commit_files > 0:
                            most_recent_commit = commit_of_interest 


                except github.RateLimitExceededException:
                    print()
                    sleep( session, "G_MORE_PR", logger )


                else:
                    # append each list of pr info to a metalist
                    pr_metalist.append( pr_info_list ) 

                    # append most recent commit to list of commits
                    commits_list.append( most_recent_commit ) 

                    # display info
                    if diagnostics == "true":

                        commit_list_len    = str( len( commits_list ))
                        num_of_commits_str = str( num_of_commits )
                        pr_list_len        = str( len( pr_metalist ))
                        row_quant_str      = str( safe_quant )

                        print( pr_num_diag + pr_num_str )
                        print( pr_list_len_diag + pr_list_len + '/' + row_quant_str )
                        print( commit_list_len_diag + commit_list_len + '/' + row_quant_str)
                        print( commits_per_pr_diag + num_of_commits_str )


                    print_rem_calls( session )

                    index += 1 


            else:
                index += 1 


        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_PR", logger )


    log_ops.complete( logger )

    return pr_metalist, commits_list 
