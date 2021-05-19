# ---------------------------------------------------------------------------
# Authors: Jacob Stuck and Jacob Penney
# Notes  : documentation for pygithub can be found @
#          https://pygithub.readthedocs.io/en/latest/index.html
# --------------------------------------------------------------------------- 


# TODO:
#   HIGH:   
#   - check to make sure that we are handling a lack of commits on a PR
#     correctly
#   - create checks to protect from lack of pull requests

#   MED:
#   - circumvent socket timeout

#   LOW:
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

RATE_LIMIT       = 102




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
#                 - github class: 
#                   -link: https://pygithub.readthedocs.io/en/latest/github.html
#--------------------------------------------------------------------------- 
def main():

    # retrieve positional arguments as variables
    ( repo_str, auth_file, output_file_name, output_type ) = get_CLI_args() 

    # get user auth info
    userauth_list = read_user_info( auth_file )  

    # authenticate the user with GitHub
    github_sesh = github.Github( userauth_list[0] )

    # display remaining calls to GitHub
    print( "\nProgram starting..." )
    print_rem_calls( github_sesh ) 
     
    # retrieve paginated list of issues and pull requests
    paged_list_tuple = get_paginated_lists( repo_str, output_type, github_sesh)

    # write output to csv file
    write_csv_output( github_sesh, output_file_name, output_type, paged_list_tuple )




#--------------------------------------------------------------------------- 
# Function name : get_CLI_args 
# Process       : adds the ability to process commandline args and a grouping
#                 of mutually exclusive args, collects and processes the args,
#                 and returns them to the user
# Parameters    : none
# Postconditions: commandline args are available to the program
# Notes         : none
# Docs          : 
#                 - topic: argparse (library)
#                   - link: https://docs.python.org/3/library/argparse.html
#--------------------------------------------------------------------------- 
def get_CLI_args():

    output_type = "commit"


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
                              help="CSV file name to write output to" )      
     
    # retrieve positional arguments
    CLI_args = arg_parser.parse_args()  

    # separate into individual variables
    repo_name = CLI_args.repo_name
    auth_file = CLI_args.auth_file
    output_file_name = CLI_args.output_file_name

    # create output string
    if CLI_args.pr:
        output_type = "pr"


    return ( repo_name, auth_file, output_file_name, output_type )




#--------------------------------------------------------------------------- 
# Function name : get_commit_info
# Process       : retrieves list of most recent commits, as commit objects,
#                 and extracts relevant info from that commit object
# Parameters    : 
#                 - name  : commit_list
#                   - type: Python list of pygithub commit objects
#                   - desc: list of commit objects containing relevant commit
#                           info
#                   - docs: https://pygithub.readthedocs.io/en/latest/github_objects/Commit.html#github.Commit.Commit
#                 - name  : session 
#                   - type: pygithub "Github" object                       
#                   - desc: instance of "Github" class used to authenticate
#                           actions/calls to GitHub in pygithub library 
#                   - docs: https://pygithub.readthedocs.io/en/latest/github.html 
#                 - name  : output_type                       
#                   - type: str                               
#                   - desc: one of two formats for CSV output 
# Postconditions: relevant commit info is available to the program
# Notes         : empty fields should be caught and populated with " =||= "
# Other Docs    : none
#--------------------------------------------------------------------------- 
def get_commit_info( commit_list, session, output_type ):

    # init variables
    commit_info_list     = []
    commit_info_metalist = []
    commit_list_index    = 0
    cur_commit   = None
    file_list            = []

    # commit list entry init
    #   This is necessary to prevent empty entries/indice misallignment 
    #   during data aggregation in write_csv_output if a commit does not
    #   exist 
    commit_author            = " =||= "
    commit_message           = " =||= "
    commit_date              = " =||= "
    commit_committer         = " =||= "
    commit_SHA               = " =||= "             
    file_list                = " =||= "             
    commit_patch_text        = " =||= "     
    commit_adds              = " =||= "
    commit_rms               = " =||= "            
    quoted_commit_status_str = " =||= "
    commit_changes           = " =||= "        


    print( "\n\nGetting commit info..." )

    while commit_list_index < RATE_LIMIT:
        try:

            # retrieve list of commits for one pr
            cur_commit = commit_list[commit_list_index] 


            if cur_commit != " =||= ":

                # get relevant author
                commit_author = cur_commit.commit.author.name
                
                # get relevant commit message
                commit_message = cur_commit.commit.message


                # prepare base list for both output types
                commit_info_list = [
                        commit_author,
                        commit_message
                        ]


                # get output type-dependent info. Appends start at index 2
                if output_type == "pr":

                    # get relevant commit date
                    commit_date = cur_commit.commit.author.date.strftime(
                                                           "%m/%d/%y %I:%M:%S %p" )

                    commit_info_list += commit_date


                else:
                    
                    # reset variables
                    commit_adds          = 0
                    commit_changes       = 0
                    commit_patch_text    = ""
                    commit_rms           = 0
                    commit_status_str    = ""
                    file_list            = []
                    
                    
                    # get relevant commit file list
                    commit_files = cur_commit.files 

                    # get relevant committer
                    commit_committer = cur_commit.commit.committer.name 

                    # get relevant commit SHA
                    commit_SHA = cur_commit.sha

                    # get relevant commit status str
                    # commit_status_str = cur_commit.status


                    # retrieve each modified file and place in list
                    for file in commit_files:
                        file_list.append( file.filename )
                        commit_adds       += int( file.additions )
                        commit_changes    += int( file.changes )
                        commit_patch_text += str( file.patch ) + ", "
                        commit_rms        += int( file.deletions )
                        commit_status_str += file.status + ", "

                    
                    quoted_commit_status_str = "\"" + commit_status_str + "\""

                    commit_info_list += [
                            commit_committer,
                            commit_SHA, 
                            file_list, 
                            commit_patch_text,
                            commit_adds,
                            commit_rms,
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
# Function name : get_issue_info
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
# Other Docs    :
#                 - topic : checking for NoneType 
#                   - link: https://stackoverflow.com/questions/23086383/how-to-test-nonetype-in-python 
#--------------------------------------------------------------------------- 
def get_issue_info( issue_list, session ):

    index              = 0
    isPR               = 0
    issue_context_list = []
    issue_metalist     = []


    print( "\n\nGetting issue info..." )

    while index < RATE_LIMIT:
        try:
            # work on one issue from paginated list at a time
            cur_issue             = issue_list[index]          

            # get info from curret issue
            issue_author_str      = str( cur_issue.user.name ) 
            issue_body_str        = str( cur_issue.body )
            issue_comment_str     = str( cur_issue.comments ) 
            issue_closed_date_str = str( cur_issue.closed_at.strftime(
                                                    "%m/%d/%y %I:%M:%S %p" ) )
            issue_title_str       = str( cur_issue.title )


            # check if the current issue has an associated PR
            if cur_issue.pull_request is not None:
                isPR = 1 
            

            # clean and quote issue body str
            issue_body_stripped = issue_body_str.strip( '\n' )
            issue_body_str      = "\"" + issue_body_stripped + "\""


            # replace empty issue comment str w/ special symbol
            if issue_comment_str == '0':
                issue_comment_str = " =||= " 


            issue_context_list  = [
                    issue_closed_date_str, 
                    issue_author_str, 
                    issue_title_str, 
                    issue_body_str,
                    issue_comment_str,
                    isPR
                    ]


            issue_metalist.append( issue_context_list )

            print_rem_calls( session )

            index += 1
        

        except github.RateLimitExceededException:
            run_timer( session )


    return issue_metalist




#--------------------------------------------------------------------------- 
# Function name : get_limit_info
# Process       : uses type_flag param to determine type of output to user;
#                   - "remaining": returns remaining calls to GitHub API
#                                  before session is rate limited. Method
#                                  belongs to "Github" class
#                   - "reset": returns the amount of time before amount of
#                              calls to GitHub API is renewed. Always starts 
#                              at one hour. Method belongs to "Github" class
# Parameters    : 
#                 - name  : session
#                   - type: pygithub "Github" object
#                   - desc: instance of "Github" class used to authenticate
#                           actions/calls to GitHub in pygithub library
#                   - docs: https://pygithub.readthedocs.io/en/latest/github.html
#                 - name  : type_flag
#                   - type: str
#                   - desc: contains the type of output asked for by user
#                           @ commandline. Can be either "pr" or "commit".
# Postconditions: rate info is available to be printed to user
# Notes         : none
# Other Docs    : none
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
# Function name : get_paginated_lists
# Process       : uses CLI str arg of repo name during call to GitHub to 
#                 retrieve pygithub repo object, uses repo object in call to 
#                 retrieve paginated list of all pull requsts associated with 
#                 that repo, and all associated issues depending on the output
#                 file desired
# Parameters    : 
#                 - name  : input_repo_str
#                   - type: str 
#                   - desc: commandline arg containing repo name
#                 - name  : output_type
#                   - type: str
#                   - desc: one of two formats for CSV output
#                 - name  : session
#                   - type: pygithub "Github" object
#                   - desc: instance of "Github" class used to authenticate
#                           actions/calls to GitHub in pygithub library
#                   - docs: https://pygithub.readthedocs.io/en/latest/github.html
# Postconditions: paginated lists of relevant info are available to program
# Notes         : utilizes try-except block to preempt code breaking due to
#                 exception thrown for rate limiting
#                   - docs: https://pygithub.readthedocs.io/en/latest/utilities.html
# Other Docs    :
#--------------------------------------------------------------------------- 
def get_paginated_lists( input_repo_str, output_type, session ):

     all_lists_retrieved = False
     issues_list         = []
     pr_list             = [] 

           
     # retrieve GitHub repo object
     repo_obj = session.get_repo( input_repo_str )  

     # loop until both lists are fully retrieved to in case of socket timout
     while all_lists_retrieved == False:
        try:
            print( "\n\nGathering GitHub data paginated lists..." )
            
            # retrieve paginated list of pull requests
            pr_list = repo_obj.get_pulls( base='master', direction='asc', 
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


     return ( issues_list, pr_list )




#--------------------------------------------------------------------------- 
# Function name : get_PR_info
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
# Other Docs    :
#--------------------------------------------------------------------------- 
def get_PR_info( pr_list, session, output_type ):

    # init variables
    commits_list       = []
    index              = 0
    most_recent_commit = " =||= "
    pr_info_list       = []
    pr_metalist        = []


    print( "\n\nGetting pull request info..." )

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
            pr_body_stripped = pr_body_str.strip( '\n' )
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


            # check for the existence of useful indices to test if 
            # a PR has commits
            last_commit_position = pr_commits.totalCount - 1

            
            # test if index value is valid
            if last_commit_position >= 0:

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
        newLine_stripped_value = value.strip( '\n' )
        
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
    
    # get the amount of time until our call amount is reset
    sleep_time = get_limit_info( session, "reset" )

    # sleep for that amount of time
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
                             lineterminator='\n' )
          

        # retrieve lists of PR and issue data
        if output_type == "pr":
            label_cols = PR_COL_NAMES

            issue_info_metalist = get_issue_info( issues_list, github_sesh )  

        
        pr_info_metalist, commits_paginated_list = get_PR_info( pr_list, 
                                                                github_sesh,
                                                                output_type )

        commit_info_metalist = get_commit_info( commits_paginated_list, 
                                                github_sesh, output_type )

        print( "\n\nWriting data..." )

        # write column labels
        writer.writerow( label_cols ) 


        # aggregate data lists into rows
        while aggregation_index < RATE_LIMIT:

            # get ecumenical values
            cur_commit     = commit_info_metalist[aggregation_index]
            commit_author  = cur_commit[0]
            commit_message = cur_commit[1] 

            cur_pr         = pr_info_metalist[aggregation_index]
            pr_num         = cur_pr[0] 


            # get output type-dependent values
            if output_type == "pr":
                cur_issue         = issue_info_metalist[aggregation_index]

                commit_date       = cur_commit[2] 

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
                #        Issue_comments, PR_Author, Commit_Author, 
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
     

    print( "\nOutput complete!" )




if __name__ == '__main__':
    main() 
 
