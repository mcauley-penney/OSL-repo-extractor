# ---------------------------------------------------------------------------
# Author: Jacob Stuck
# Purpose:
# Process: 
# Notes: documentation can be found @:
#   - Github: https://pygithub.readthedocs.io/en/latest/github.html
# --------------------------------------------------------------------------- 


# TODO:
#   - clean constants
#   - clean annotations
#   - add arg_parser description


# imports
import argparse
import csv
from os import WEXITED
from github import Github


# constants
COMMA       = ','
DESCRIPTORS = (
        "PR_Number,Issue_Closed_Date, Issue_Author, Issue_Title, Issue_Body,"
        " Issue_comments, PR_Closed_Date,PR_Author, PR_Title, PR_Body,"
        " PR_Comments, Commit_Author, Commit_Date, Commit_Message, isPR"
         )
NEW_LINE    = '\n'
OUTPUT_DASH = "---------------------"
RATE_LIMIT  = 5
READ        = 'r' 
WRITE       = 'w'




def main():
    # metalist of output data
    data_metalist= []

    #Pull request related lists
    pr_num_list = []

    #Issue related lists
    issue_authors_list = []
    issue_bodies_list = []
    issue_closed_dates_list = []
    isssue_comments_list = []
    issue_titles_list = []
 


    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="TODO" ) 
      

    # add repo input CLI arg
    arg_parser.add_argument( 'input_file', type=str,  
                              help="""text file containing properly 
                              formatted arguments""" ) 


    # add auth token CLI arg
    arg_parser.add_argument( 'auth_file', type=str, 
                              help="""text file containing user 
                              authentification info""" ) 


    arg_parser.add_argument( 'output_file_name', type=str, 
                              help="CSV file to write output to" )      
     

    # retrieve positional arguments as variables
    CLI_args = arg_parser.parse_args() 
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
    pr_paginated_list = repo_input_paginated_list.get_pulls( 
                                state='open', sort='created', base='master' )

    issues_paginated_list = repo_input_paginated_list.get_issues(state="closed")


    # Open the output csv file in preparation for writing
    with open( output_file_name, WRITE, newline="", encoding="utf-8") as csvfile:
        writer = csv.writer( 
                csvfile, quoting=csv.QUOTE_NONE, delimiter=' ', 
                quotechar='', escapechar='\\', lineterminator='\n' 
                )


        # sets up the table
        writer.writerow( [DESCRIPTORS] )


        # Calls in
        pr_num_list = getPRNumber( pr_paginated_list )
        # closedDates = getIssueClosedDate( pr_paginated_list )
        issue_authors_list = getIssueAuthor( issues_paginated_list )
        issue_titles_list = getIssueTitle( issues_paginated_list )
        issue_bodies_list = getIssueBody( issues_paginated_list )


        writer.writerow( ' '.join( pr_num_list ) )


        #list of lists of all the data that has been collected
        # data_metalist = [
        #         pr_num_list, 
        #         issue_closed_dates, 
        #         issue_authors, 
        #         issue_titles, 
        #         issue_bodies
        #         ]

        



# ---------------------------------------------------------------------------
# Function: getPRNumber
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def getPRNumber( pulls ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        print( pulls[index].number )

        prStr = str( pulls[index].number ) + ","
        print(prStr)

        outList.append(prStr)
        index+=1


    print(OUTPUT_DASH + "\nloop exit-PRNumber\n" + OUTPUT_DASH)

    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# --------------------------------------------------------------------------- 
def getIssueClosedDate( issue_list ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        cur_issue = issue_list[index]
        issueDateStr = str( cur_issue.closed_at )
        print(issueDateStr)

        outList.append(issueDateStr)
        index+=1

    
    print( OUTPUT_DASH + "loop exit-closedDates" + OUTPUT_DASH)

    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------  
def getIssueAuthor( issue_list ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        cur_issue = issue_list[index]
        issueAuthorStr = str( cur_issue.user.name )
        print(issueAuthorStr)

        outList.append(issueAuthorStr)
        index+=1


    print( OUTPUT_DASH + "loop exit-IssueAuthor" + OUTPUT_DASH )

    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------   
def getIssueTitle( issue_list ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        issueTitleStr = str( issue_list[index].title )
        print( "Getting issue title at index: " + str( index ) )

        outList.append( issueTitleStr )
        index+=1


    print( OUTPUT_DASH + "loop exit-IssueTitle" + OUTPUT_DASH )

    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def getIssueBody( issue_list ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        issueBodyStr = str( issue_list[index].body )
        print( "getting body at index:" + str( index ) )

        outList.append( issueBodyStr )
        index+=1


    print(OUTPUT_DASH + "loop exit-IssueBody" + OUTPUT_DASH )

    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def getIssueComments( issue_list ):
    outList = []
    index = 0

    while index < RATE_LIMIT:
        issueCommentStr = str(issue_list[index].comments)
        print( "getting comments at index:" + str( index ) )

        outList.append( issueCommentStr )
        index+=1


    print( OUTPUT_DASH + "loop exit-IssueComments" + OUTPUT_DASH )

    return outList




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

    # read contents out of file
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
 



if __name__ == '__main__':
    main() 
