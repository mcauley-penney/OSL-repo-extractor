# ---------------------------------------------------------------------------
# Author: Jacob Stuck and Jacob Penney
# Purpose:
# Process: 
# Notes: documentation can be found @:
#   - Github: https://pygithub.readthedocs.io/en/latest/github.html
# --------------------------------------------------------------------------- 


# TODO:
#   - clean annotations
#   - add arg_parser description
#   - create checks to protect from lack of pull requests
#   - get issue info in one loop?




# imports
import argparse
import csv
from github import Github


# constants
COMMA       = ','
NEW_LINE    = '\n'
RATE_LIMIT  = 5
READ        = 'r' 




def main():

    print( "Gathering GitHub data...\n" )

    # retrieve positional arguments as variables
    CLI_args = get_args() 

    repo_input_file_to_open = CLI_args.input_file
    userauth_file_to_open = CLI_args.auth_file
    output_file_name =  CLI_args.output_file_name


    # get repo inputs
    repo_list = create_input_list( repo_input_file_to_open )  
    test_repo = repo_list[0]


    # get user info
    userauth_list = read_user_info( userauth_file_to_open ) 


    # authenticate with GitHub
    git_session = Github( userauth_list[0] )
    

    # retrieve paginated list of repos
    repo_input_paginated_list = git_session.get_repo( test_repo )


    # retrieve paginated list of pull requests
    pr_paginated_list = repo_input_paginated_list.get_pulls( base='master',  
                                               direction='asc', sort='created',
                                               state='all' )

    
    # retrieve paginated list of issues
    issues_paginated_list = repo_input_paginated_list.get_issues(direction='asc',
                                                sort='created', state='closed' )
     
    print( "Writing data...\n" )
     
    # write output to csv file
    write_csv_output( issues_paginated_list, output_file_name, pr_paginated_list )
    



# ---------------------------------------------------------------------------
# Function: create_input_list 
# Process: accepts the name of a file to open, opens the file, reads its
#          contents out, and processes that content into a list
# Parameters: name of the file to open
# Postcondition: returns a list of input from the input text
# Exceptions: none 
# Note: none
# ---------------------------------------------------------------------------
def create_input_list( fileToOpen ):
 
    # variables
    repo_list = []


    # open file
    repo_input_file_obj = open( fileToOpen, READ )

    # read contents out
    api_input_contents = repo_input_file_obj.readlines()

    for line in api_input_contents:
        # strip rows of new line characters
        newLine_stripped_line = line.strip( NEW_LINE )

        # strip rows of quote characters
        quote_stripped_line = newLine_stripped_line.replace( '"', '' )

        # strip lines on commas to create list of items
        repo_list = quote_stripped_line.split( COMMA )


    # close file 
    repo_input_file_obj.close()


    return repo_list



 
#--------------------------------------------------------------------------- 
# Function name : get_args 
# Process       : 
# Parameters    : 
# Postconditions: 
# Notes         : 
#--------------------------------------------------------------------------- 
def get_args():

    # TODO
    #   add mutex arg for diff filetype

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="TODO" ) 
      

    # add repo input CLI arg
    arg_parser.add_argument( 'input_file', type=str,  
                              help="""text file containing properly formatted 
                              arguments""" ) 


    # add auth token CLI arg
    arg_parser.add_argument( 'auth_file', type=str, 
                              help="""text file containing user 
                              authentification info""" ) 


    arg_parser.add_argument( 'output_file_name', type=str, 
                              help="CSV file to write output to" )      
     

    # retrieve positional arguments as variables
    CLI_args = arg_parser.parse_args()  


    return CLI_args



 

 
# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------  
def get_issue_author( issue_list ):
    outList = []
    index   = 0

    while index < RATE_LIMIT:
        cur_issue = issue_list[index]
        issueAuthorStr = str( cur_issue.user.name )

        outList.append( issueAuthorStr )
        index += 1


    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def get_issue_body( issue_list ):
    outList = []
    index   = 0

    while index < RATE_LIMIT:
        cur_issue = cur_issue = issue_list[index]
        issue_body_str = str( cur_issue.body )

        stripped_issue_body_str = issue_body_str.replace( '\\', '' )

        out_issue_body_str = "\"" + stripped_issue_body_str + "\""

        outList.append( out_issue_body_str  )
        index += 1


    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# --------------------------------------------------------------------------- 
def get_issue_closedDate( issue_list ):
    outList = []
    index   = 0

    while index < RATE_LIMIT:
        cur_issue = issue_list[index]
        issueDateStr = str( cur_issue.closed_at )

        outList.append( issueDateStr )
        index += 1

    
    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def get_issue_comments( issue_list ):
    outList = []
    index   = 0

    while index < RATE_LIMIT:
        cur_issue = issue_list[index]
        issueCommentStr = str( cur_issue.comments )

        outList.append( issueCommentStr )
        index += 1


    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------   
def get_issue_title( issue_list ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        cur_issue = issue_list[index]
        issueTitleStr = str( cur_issue.title )

        outList.append( issueTitleStr )
        index+=1


    return outList




# ---------------------------------------------------------------------------
# Function: get_PR_init_info
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def get_PR_init_info( pr_list ):
    outList = []
    index   = 0

    while index < RATE_LIMIT:
        cur_pr = pr_list[index]
        pr_num = str( cur_pr.number ) 

        outList.append( pr_num )
        index+=1


    return outList




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
    userinfo_file_obj = open( userinfo_file, READ )

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
 



# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def write_csv_output( issues_list, output_file_name, pr_list ):
    # index for aggregation loop
    aggregation_index       = 0

    # data lists
    issue_authors_list      = []
    issue_bodies_list       = []
    issue_closed_dates_list = []
    isssue_comments_list    = []
    issue_titles_list       = []
    pr_num_list             = []  
 

    # Open the output csv file in preparation for writing
    with open( output_file_name, 'w', newline="", 
                                                encoding="utf-8" ) as csvfile:
        writer = csv.writer( 
                csvfile, quoting=csv.QUOTE_NONE, delimiter='\a', 
                quotechar='', escapechar='\\', lineterminator=NEW_LINE )


        # write labels at top of output
        writer.writerow( ["PR_Number", "Issue_Closed_Date", "Issue_Author",
                          "Issue_Title", "Issue_Body", "Issue_comments", 
                          "PR_Closed_Date,PR_Author, PR_Title, PR_Body",
                          "PR_Comments", "Commit_Author", "Commit_Date", 
                          "Commit_Message", "isPR"] )


        # retrieve lists of PR and issue data
        pr_num_list = get_PR_init_info( pr_list )

        issue_closed_dates_list = get_issue_closedDate( issues_list )
        issue_authors_list = get_issue_author( issues_list )
        issue_titles_list = get_issue_title( issues_list )
        issue_bodies_list = get_issue_body( issues_list )

        
        # aggregate data lists into rows
        while aggregation_index < RATE_LIMIT:
            issue_author = issue_authors_list[aggregation_index]
            issue_body = issue_bodies_list[aggregation_index] 
            issue_closed_date = issue_closed_dates_list[aggregation_index] 
            issue_title = issue_titles_list[aggregation_index] 
            pr_num = pr_num_list[aggregation_index] 


            # print rows to output file 
            # output_row = [ pr_info, issue_title, issue_author ]
        
            writer.writerow( [ pr_num, issue_closed_date, issue_title,
                               issue_body, issue_author ] )

            aggregation_index += 1
     



if __name__ == '__main__':
    main() 