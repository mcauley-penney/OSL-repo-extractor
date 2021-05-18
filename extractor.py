# ---------------------------------------------------------------------------
# Author: Jacob Stuck and Jacob Penney
# Purpose:
# Process: 
# Notes: documentation for pygithub can be found @:
#   - Github: https://pygithub.readthedocs.io/en/latest/github.html
# --------------------------------------------------------------------------- 

# TODO:
#   - features ( by priority ):
#       - for PR output, need:
#           - isPR

#       - for Commit output, need: 
#           - Author_Login
#           - Committer_login    DONE:
#           - PR_Number          DONE:
#           - SHA                DONE: 
#           - Commit_Message     DONE: 
#           - File_name          DONE: 
#           - Patch_text
#           - Additions
#           - Deletions
#           - Status
#           - Changes

#       - for Commit output, need: 
#           - All 🙃 
#       - create checks to protect from lack of pull requests
#       - transcend rate limit
#       - circumvent socket timeout
#   
#   -TODAY:
#       - rewrite output function                        DONE:
#       - begin adding functionality for commit file     DONE: 
#   
# 
#   - post-completion:
#       - clean spacing
#       - clean annotations
#       - clean comments
#       - add arg_parser description 


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

PR_COL_NAMES     = ["PR_Number", "Issue_Closed_Date", "Issue_Author",
                    "Issue_Title", "Issue_Body", "Issue_comments", 
                    "PR_Closed_Date,PR_Author, PR_Title, PR_Body",
                    "PR_Comments", "Commit_Author", "Commit_Date", 
                    "Commit_Message", "isPR"]

NEW_LINE         = '\n'
RATE_LIMIT       = 5        




#--------------------------------------------------------------------------- 
# Function name : driver
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def main():

    # retrieve positional arguments as variables
    ( repo_str, auth_file, output_file_name, output_type ) = get_args() 


    # get user info
    userauth_list = read_user_info( auth_file )  


    # authenticate with GitHub
    github_sesh = github.Github( userauth_list[0] )
    # github_sesh = github.Github(  )
     

    # retrieve paginated list of repos
    repo_paginated_list = github_sesh.get_repo( repo_str ) 


    # retrieve paginated list of issues and pull requests
    paged_list_tuple = get_paginated_lists( repo_paginated_list, github_sesh)


    # write output to csv file
    write_csv_output( github_sesh, output_file_name, output_type, paged_list_tuple )




#--------------------------------------------------------------------------- 
# Function name : get_args 
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_args():

    output_type = ""

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="TODO" ) 
    
    # establish mutually exclusive argument capability
    mutually_excl_args = arg_parser.add_mutually_exclusive_group()  

    # add mutually exclusive args to choose output type
    mutually_excl_args.add_argument( '-p', '--pr', action="store_true",
                                     help="Create \"pull request\" type file" )

    mutually_excl_args.add_argument( '-c', '--commit', action="store_true",
                                     help="Create \"commit\" type file" )  

    # add repo input CLI arg
    arg_parser.add_argument( 'repo_name', type=str,  
                              help="repo name in the format \"user/repo\"" ) 

    # add auth token CLI arg
    arg_parser.add_argument( 'auth_file', type=str, 
                              help="""text file containing user 
                              authentification info""" ) 

    # add output file name CLI arg
    arg_parser.add_argument( 'output_file_name', type=str, 
                              help="CSV file to write output to" )      
     
    # retrieve positional arguments
    CLI_args = arg_parser.parse_args()  

    # separate into individual variables
    repo_name = CLI_args.repo_name
    auth_file = CLI_args.auth_file
    output_file_name = CLI_args.output_file_name

    # create output string
    if CLI_args.pr:
        output_type = "pr"

    elif CLI_args.commit:
        output_type = "commit"


    return ( repo_name, auth_file, output_file_name, output_type )




#--------------------------------------------------------------------------- 
# Function name : get_commit_info
# Process       : retrieves the most recent commit from the current pull
#                 request
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_commit_info( commit_paged_list, session, output_type ):

    # init variables
    commit_info_list      = []
    commit_info_metalist  = []
    commit_metalist_index = 0
    commit_of_interest    = None
    file_list             = []


    print( "Getting commit info..." )

    while commit_metalist_index < RATE_LIMIT:
        try:
            
            # retrieve list of commits for one pr
            cur_commit_list = commit_paged_list[commit_metalist_index]

            # get the last actionable index for that list
            last_position = cur_commit_list.totalCount - 1

            # retrieve commit of interest from that position
            commit_of_interest = cur_commit_list[last_position]
            

            # get relevant author
            commit_author = commit_of_interest.commit.author.name
            
            # get relevant commit message
            commit_message = commit_of_interest.commit.message


            # prepare base list for both output types
            commit_info_list = [
                    commit_author,
                    commit_message
                    ]


            # get output type-dependent info, starts at index 2
            if output_type == "pr":

                # get relevant commit date
                commit_date = commit_of_interest.commit.author.date.strftime(
                                                       "%m/%d/%y %I:%M:%S %p" )

                commit_info_list += [commit_date]

            else:
                
                # reset file list
                file_list = []

                # get relevant commit SHA
                commit_SHA = commit_of_interest.sha

                # get relevant commit file list
                commit_files = commit_of_interest.files

                # retrieve each modified file and place in list
                for file in commit_files:
                    file_list.append( file.filename )
                    print_rem_calls( session )


                commit_info_list += [commit_SHA, file_list]


            commit_info_metalist.append( commit_info_list )

            print_rem_calls( session )
 
            commit_metalist_index += 1


        except github.RateLimitExceededException:
            run_timer( session ) 


    print('\n')


    return commit_info_metalist



 
#--------------------------------------------------------------------------- 
# Function name : get_issue_info
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_issue_info( issue_list, session ):

    index              = 0
    issue_context_list = []
    issue_metalist     = []


    print( "Getting issue info..." )

    while index < RATE_LIMIT:
        try:
            cur_issue             = issue_list[index]          # here
            issue_author_str      = str( cur_issue.user.name ) # here
            issue_body_str        = str( cur_issue.body )
            issue_comment_str     = str( cur_issue.comments ) 
            issue_closed_date_str = str( cur_issue.closed_at.strftime(
                                                    "%m/%d/%y %I:%M:%S %p" ) )
            issue_title_str       = str( cur_issue.title )
            

            issue_body_stripped = issue_body_str.strip( NEW_LINE )
            issue_body_str      = "\"" + issue_body_stripped + "\""
            
            if issue_comment_str == '0':
                issue_comment_str = " =||= " 

            issue_context_list  = [
                    issue_closed_date_str, 
                    issue_author_str, 
                    issue_title_str, 
                    issue_body_str,
                    issue_comment_str 
                    ]


            issue_metalist.append( issue_context_list )

            print_rem_calls( session )

            index += 1
        

        except github.RateLimitExceededException:
            run_timer( session )


    print('\n')


    return issue_metalist




#--------------------------------------------------------------------------- 
# Function name : get_limit_info
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_limit_info( session, type_flag ):

    out_rate_info = None


    if type_flag == "remaining":

        # get remaining calls before reset from GitHub API
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
# Function name : get_paginated_lists
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_paginated_lists( input_repo, session ):

     all_lists_retrieved = False
     issues_list         = []
     pr_list             = [] 


     # loop until both lists are fully retrieved to reset in case of 
     # socket timout
     while all_lists_retrieved == False:
        try:
            print( "Gathering GitHub data paginated lists...\n" )

            # retrieve paginated list of issues
            issues_list = input_repo.get_issues( direction='asc',
                                                 sort='created', 
                                                 state='closed' )

            # retrieve paginated list of pull requests
            pr_list = input_repo.get_pulls( base='master', direction='asc', 
                                            sort='created', state='all' )

            all_lists_retrieved = True


        except github.RateLimitExceededException:
            run_timer( session ) 


     return ( issues_list, pr_list )




#--------------------------------------------------------------------------- 
# Function name : get_PR_info
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_PR_info( pr_list, session, output_type ):

    # init variables
    index           = 0
    commits_paginated_metalist = []
    pr_info_list    = []
    pr_metalist     = []


    print( "Getting pull request info..." )

    while index < RATE_LIMIT:
        try:
            cur_pr = pr_list[index]

            pr_author_str      = str( cur_pr.user.login ) 
            pr_body_str        = str( cur_pr.body )
            pr_closed_date_str = str( cur_pr.closed_at )
            pr_comment_str     = str( cur_pr.comments )
            pr_num_str         = str( cur_pr.number ) 
            pr_title_str       = str( cur_pr.title ) 

            # get paginated list of commits for each pr
            pr_commits         = cur_pr.get_commits()

            #  clean each pr body of new line chars and place in quotes
            pr_body_stripped = pr_body_str.strip( NEW_LINE )
            pr_body_str = "\"" + pr_body_stripped + "\"" 

            # add special string in place of empty comments
            if pr_comment_str == '0':
                pr_comment_str = " =||= "

            # each output type will require the pr num, so treat as default
            pr_info_list = [
                    pr_num_str
                    ]  

            # add content based on output type
            if output_type == "pr":
                pr_info_list += [
                        pr_author_str,
                        pr_body_str,
                        pr_closed_date_str,
                        pr_comment_str,
                        pr_title_str,
                        ]

            # append each list of pr info to a metalist
            pr_metalist.append( pr_info_list )

            # append each paginated list of commits to a metalist
            commits_paginated_metalist.append( pr_commits )

            # display remaining calls
            print_rem_calls( session )

            index+=1


        except github.RateLimitExceededException:
            run_timer( session ) 

    
    print('\n')


    return pr_metalist, commits_paginated_metalist




#--------------------------------------------------------------------------- 
# Function name : print_rem_calls 
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def print_rem_calls( session ):

    # get remaining calls before reset
    remaining_calls = get_limit_info( session, "remaining" )

    # format as a string
    rem_calls_str = '{:4d}'.format( remaining_calls ) 

    # print output in place
    print( "    calls left: " + str( rem_calls_str ), end="\r" )  




# ---------------------------------------------------------------------------
# Function: read_user_info
# Process: open the provided text file, read out user info, and return it as
#          a string or list
# Parameters: text file containing user info
# Postcondition: returns variables holding user info
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def read_user_info( userinfo_file ):

    # variables
    parsed_userinfo_list = []


    # open text file
    userinfo_file_obj = open( userinfo_file, 'r' )

    # read contents out of file object
    userinfo_list = userinfo_file_obj.readlines()

    # loop through items in list 
    for value in userinfo_list:
        
        # remove newline chars from each item in list
        newLine_stripped_value = value.strip( NEW_LINE )
        
        # remove leading and trailing whitespaces from user info
        space_stripped_value = newLine_stripped_value.strip()

        # place each item into a new list if it has content
        if len( space_stripped_value ) > 0:
            parsed_userinfo_list.append( space_stripped_value )


    return parsed_userinfo_list




#--------------------------------------------------------------------------- 
# Function name : run_timer 
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def run_timer( session ):
    sleep_time = get_limit_info( session, "reset" )
    timer( sleep_time ) 




#--------------------------------------------------------------------------- 
# Function name : timer
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def timer( countdown_time ):

    while countdown_time > 0:
        
        # cast float value to an int
        int_time = int( countdown_time )

        # modulo function returns time tuple  
        minutes, seconds = divmod( int_time, 60 )

        # format the time string before printing
        countdown = '{:02d}:{:02d}'.format( minutes, seconds )

        # print time string on the same line as before
        print( "Time until calls can be made: " + countdown, end="\r" )

        time.sleep( 1 )
        countdown_time -= 1




#--------------------------------------------------------------------------- 
# Function name : write_csv_output
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def write_csv_output( github_sesh, output_file_name, output_type, list_tuple ):

    # unpack lists
    issues_list, pr_list = list_tuple

    # index for aggregation loop
    aggregation_index   = 0

    # data lists
    commit_info_metalist = []
    issue_info_metalist  = []  
    output_row           = []
    pr_info_metalist     = []  

    # output columns
    label_cols = COMMIT_COL_NAMES
 

    # Open the output csv file in preparation for writing
    with open( output_file_name, 'w', newline="", encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_NONE, delimiter='\a', 
                             quotechar='', escapechar='\\', 
                             lineterminator=NEW_LINE )
          

        # retrieve lists of PR and issue data
        if output_type == "pr":
            label_cols = PR_COL_NAMES

            issue_info_metalist = get_issue_info( issues_list, github_sesh )  

        
        pr_info_metalist, commits_paginated_list = get_PR_info( pr_list, 
                                                                github_sesh,
                                                                output_type )

        commit_info_metalist = get_commit_info( commits_paginated_list, 
                                                github_sesh, output_type )

        print( "Writing data...\n" )

        # write column labels
        writer.writerow( label_cols ) 


        # aggregate data lists into rows
        while aggregation_index < RATE_LIMIT:

            # get ecumenical values
            cur_commit     = commit_info_metalist[aggregation_index]
            commit_author  = cur_commit[0]
            commit_message = cur_commit[1] 

            cur_pr          = pr_info_metalist[aggregation_index]
            pr_num          = cur_pr[0] 


            # get output type-dependent values
            if output_type == "pr":
                cur_issue         = issue_info_metalist[aggregation_index]

                commit_date    = cur_commit[2] 

                issue_closed_date = cur_issue[0] 
                issue_author      = cur_issue[1]
                issue_title       = cur_issue[2]
                issue_body        = cur_issue[3] 
                issue_comments    = cur_issue[4]  

                pr_author       = cur_pr[1] 
                pr_body         = cur_pr[2] 
                pr_closed_date  = cur_pr[3] 
                pr_comments     = cur_pr[4] 
                pr_title        = cur_pr[5] 


                # order: PR_Number, Issue_Closed_Date, Issue_Author,  
                #        Issue_Title, Issue_Body, PR_Closed_Date,     
                #        RR_Title, PR_Body, PR_Comments               
                #        Issue_comments, PR_Author, Commit_Author, 
                #        Commit_Date, Commit_Message, isPR
                # ------------------------------------------------------------
                output_row = [pr_num, issue_closed_date, issue_author,  
                              issue_title, issue_body, pr_closed_date,   
                              pr_title, pr_body, pr_comments,            
                              issue_comments, pr_author, commit_author,  
                              commit_date, commit_message]               

            else:
                commit_SHA       = cur_commit[2]
                commit_file_list = cur_commit[3]


                # order:  Author_Login, Committer_login, PR_Number,
                #         SHA, Commit_Message, File_name,
                #         Patch_text, Additions, Deletions,
                #         Status, Changes
                # ------------------------------------------------------------
                output_row = [commit_author, pr_num,
                              commit_SHA, commit_message, commit_file_list]


            writer.writerow( output_row ) 
                             
            aggregation_index += 1
     



if __name__ == '__main__':
    main() 
 
