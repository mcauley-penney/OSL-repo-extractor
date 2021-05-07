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


import argparse
import csv
from github import Github


# constants
COMMA       = ','
NEW_LINE    = '\n'
RATE_LIMIT  = 5
READ        = 'r' 
WRITE       = 'w'


# pull request related apis
# pr = repo_list.get_pulls()
# 
# # issue related apis
# issue = repo_list.get_issues()
# issues = repo_list.get_issues(state="closed")

#complete list
data = []

#Pull request related lists
prNumL = []

#Issue related lists
issueClosedDates = []
issueAuthors = []
issueTitles = []
issueBodies = []
isssueComments = []


def main():
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


    # Open the output csv file in preparation for writing
    with open( output_file_name, WRITE, newline="", encoding="utf-8") as csvfile:
        writer = csv.writer( csvfile, quoting=csv.QUOTE_NONE, delimiter='|', 
                            quotechar='', escapechar='\\', 
                            lineterminator='\n' )

        #Gets written to the top of each column.
        descriptors = """PR_Number,Issue_Closed_Date, Issue_Author, Issue_Title,
                       Issue_Body, Issue_comments, PR_Closed_Date,PR_Author, 
                       PR_Title, PR_Body, PR_Comments, Commit_Author, 
                       Commit_Date, Commit_Message, isPR"""


        # sets up the table
        writer.writerow( [descriptors] )

        # Calls in
        prData = getPRNumber( pr_paginated_list )
        # closedDates = getIssueClosedDate( pr_paginated_list )
        issueAuthors = getIssueAuthor( pr_paginated_list )
        issueTitles = getIssueTitle( pr_paginated_list )
        issueBodies = getIssueBody( pr_paginated_list )

        #list of lists of all the data that has been collected
        data = [prNumL, issueClosedDates, issueAuthors, issueTitles, issueBodies]


        #iterates over prData and writes the first row
        for prIndex in prData:
            writer.writerow([prIndex])




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

    for pr in pulls:

       if index < RATE_LIMIT:
          ftitle = ''
          print(pr.number)
          prStr = str(pr.number) + "," + ftitle
          print(prStr)
          outList.append(prStr)
          index+=1
       else:
           print("---------------------")
           print("loop exit-PRNumber")
           print("---------------------")
           break
    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# --------------------------------------------------------------------------- 
def getIssueClosedDate(  ):
    outList = []
    index = 0

    for issue in issues:
        if index < RATE_LIMIT:
           issueDateStr = str(issue.closed_at)
           print(issueDateStr)
           outList.append(issueDateStr)
           index+=1
        else:
            print("---------------------")
            print("loop exit-closedDates")
            print("---------------------")
            break
    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------  
def getIssueAuthor(  ):
    outList = []
    index = 0

    for issue in issues:
        if index < RATE_LIMIT:
           issueAuthorStr = str(issue.user.name)
           print(issueAuthorStr)
           outList.append(issueAuthorStr)
           index+=1
        else:
            print("---------------------")
            print("loop exit-IssueAuthor")
            print("---------------------")
            break
    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------   
def getIssueTitle(inLimit):
    outList = []
    index = 0

    for issue in issues:
        if index < RATE_LIMIT:
           issueTitleStr = str(issue.title)
           print("Getting issue title at index: "+str(index))
           index+=1
           outList.append(issueTitleStr)
        else:
            print("-----------------")
            print("loop exit-IssueTitle")
            print("-----------------")
            break
    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def getIssueBody(  ):
    outList = []
    index = 0

    for issue in issues:
        if index < RATE_LIMIT:
           issueBodyStr = str(issue.body)
           print("getting body at index:" + str(index))
           index+=1
           outList.append(issueBodyStr)
        else:
            print("---------------")
            print("loop exit-IssueBody")
            print("---------------")
            break
    return outList




# ---------------------------------------------------------------------------
# Function: 
# Process: 
# Parameters: 
# Postcondition: 
# Exceptions: none
# Note: none
# ---------------------------------------------------------------------------
def getIssueComments(  ):
    outList = []
    index = 0

    for issue in issues:
        if index < RATE_LIMIT:
           issueCommentStr = str(issue.comments)
           print("getting comments at index:"+str(index))
           index+=1
           outList.append(issueCommentStr)
        else:
            print("--------------")
            print("loop exit-IssueComments")
            print("--------------")
            break
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
