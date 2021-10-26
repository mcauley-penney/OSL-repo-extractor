# ---------------------------------------------------------------------------
# Authors: Jacob Penney
# Notes  : documentation for pygithub can be found @
#          https://pygithub.readthedocs.io/en/latest/index.html
# ---------------------------------------------------------------------------

# TODO:
# 1. create instruction manual
# 2. Include delimiter config option
#
# DOC IDEAS
#   - see create_master_json context annotation
#   - discuss branches and how they can determine data grabbed
#       - how master and main may be available even though not shown
#   - With how this is coded now, your sleep functions WILL NOT count if your
#     OS or internal clock is off. Check your UEFI menu if sleep will not work
#   - If PR list len is less than total, it was reduced by check for merged





# imports
import argparse
import csv
import github
import json
import logging
import os
import time


# constants
DASHES      = "-----------------------------------------------------------"
BKBLU       = "\033[1;38;5;15;48;2;0;111;184m"
BKGRN       = "\033[1;38;5;0;48;2;16;185;129m"
BKRED       = "\033[1;38;5;0;48;2;240;71;71m"
BKYEL       = "\033[1;38;5;0;48;2;251;191;36m"
NAN         = "NaN"
NL          = '\n'
TXTRST      = "\033[0;0m"
TAB         = "    "
TIME_FRMT   = "%D, %I:%M:%S %p"

LOG_BAR     = DASHES + DASHES
DIAG_MSG    = TAB + BKYEL +" [Diagnostics]: " + TXTRST + ' '
NL_TAB      = NL + TAB
SUCCESS_MSG = BKGRN + "%s" + TXTRST
ERR_MSG     = BKRED + " Error: " + TXTRST
INFO_MSG    = NL_TAB + BKBLU + " Info: " + TXTRST
EXCEPT_MSG  = NL_TAB + BKRED + " Exception: " + TXTRST

CONF_ERR = """Incorrect configuration!

Below is the list of configurations passed to the program.
This error transpired before logging capabilities could be
established. No log has been produced for this run and the
traceback below will not be documented.
"""

CSV_PROMPT = """
Please choose type of CSV:
    [1] Pull Request
    [2] Commit
    [3] Both

    Execute """

HEADER = """
    PROGRAM START
    -------------
    Config used:
        - config file name  : %s
        - repo              : %s
        - auth file         : %s
        - rows              : %s
        - issue state       : %s
        - pr state          : %s
        - diagnostics       : %s
        - log file          : %s
        - issue json file   : %s
        - pr JSON file      : %s
        - commit JSON file  : %s
        - master JSON file  : %s
        - "pr" CSV file     : %s
        - "commit" CSV file : %s
        - "pr" separator    : %s
        - "commit" separator: %s
"""

PROG_INTRO = """
GITHUB REPO EXTRACTOR
---------------------
Please choose type of operation:
    [1] get issue JSON list
    [2] get pull request and commit JSON lists
    [3] collate JSON lists into unified JSON list
    [4] compile CSV outputs
    [5] Execute all functionality

    Execute """




#---------------------------------------------------------------------------
# Name          : driver
# Process       : 1) get config file path from CLI
#                 2) read settings out of cfg file,
#                 3) init logging
#                 4) authenticate user and establishes connection to GitHub
#                 5) begin program using exe_menu function
#
# Parameters    : none, but info retrieved from commandline
# Postconditions: program is started
# Notes         : The try-except block that contains the call to exe_menu
#                 acts as a top-level catch for any exception that is
#                 unspecified at other parts in the tree of processes that
#                 connect to exe_menu. If the program succeeds, it prints
#                 a success message and, in any outcome, it prints an end
#                 message to the log
# Other Docs    :
#                 - topic: github class, e.g. "session" variable
#                   -link: https://pygithub.readthedocs.io/en/latest/github.html
#---------------------------------------------------------------------------
def main():

    # init vars
    end_prog          = NL + "END OF PROGRAM RUN" + NL + LOG_BAR + NL
    prog_start_log    = NL + LOG_BAR + NL + "START OF PROGRAM RUN"
    unspec_except_str = TAB  + "Unspecified exception! Please see log file:"


    # subprocess 1
    config_file_name = get_CLI_args()

    # subprocess 2
    cfg_list = read_config( config_file_name )

    # subprocess 3
    log_filename = cfg_list[7]
    logger       = init_logger( log_filename )

    # begin logging
    logger.info( prog_start_log )

    # determine if user wants diagnostics
    diagnostics   = cfg_list[6]

    if diagnostics == "true":
        log_and_print( "R_CFG_DONE", "INFO", logger  )
        complete( logger )


    # subprocess 4
    authfile_name = cfg_list[2]
    session       = verify_auth( authfile_name, diagnostics, logger )

    # subprocess 5
    try:
        exe_menu( cfg_list, session, logger )

    except:
        logger.exception( NL_TAB + "Unspecified exception:\n\n" )

        print( NL + EXCEPT_MSG )
        print( unspec_except_str + NL_TAB + TAB + log_filename + NL )

    else:
        repo_name = cfg_list[1]

        log_and_print( "SUCCESS", "INFO", logger )
        print( "Operations complete for repo \"" + repo_name + "\"." )
        print( "See " + log_filename + " for operation notes!" + NL )

    finally:
        logger.info( end_prog )




#---------------------------------------------------------------------------
# Name   : check_row_quant_safety
# Context: This function is implemented inside of getter functions to
#          provide a means of determining if the amount of rows asked for
#          in the configuration file is acceptable. The row quant has to be
#          checked for different types of data, e.g. asking for 1,000 rows
#          for a repo with 1,001 issues is okay, but if that same repo only
#          has 999 PRs, we have to dial that value back to match.
#          Normalizing our config info this way allows us to avoid asking
#          the user for different values for issues and PRs
#
# Process: 1) use conditionals to determine appropriate amount of rows
#             to act upon in parent getter function:
#
#             a) if the cfg row setting asks for "all" or is an integer value
#                that is equal to or greater than the amount of rows that
#                actually exist for a given paginated list, return the maximum
#                number of datum that can be gathered using the totalCount
#                attribute of the paginated list
#             b) if the cfg row setting asks for less datum than exists,
#                return that value as an integer ( must cast it from str )
#             c) else, return that the cfg row setting is invalid
#
# Params : 1) paged_list:
#           - type: paginated list
#           - desc: a paginated list of data, from GitHub, that we
#                   want to check the length of, e.g. paginated list
#                   of issues of PRs
#
#          2) config_quant
#           - type: string
#           - desc: the amount of rows of data to retrieve from the repo,
#                   as specified by the user in the config file
#
#          3) log_msg
#           - type: string
#           - desc: a message to send to log_and_print. It describes that
#                   the row quant is being validated and which set of data
#                   it is being validated for
#
#          4) diagnostics
#           - type: string
#           - desc: a string that acts as a boolean flag. Tells the
#                   program that we want diagnostic information printed to
#                   the console
#
#          5) logger
#           - type: Python Logger object
#           - desc: Used for logging operations
#           - docs: https://docs.python.org/3/howto/logging.html#loggers
#
# Output : returns an integer to be used as the amount of rows of data to
#          gather
# Notes  : None
# Docs   : 1) totalCount attribute
#           - https://github.com/PyGithub/PyGithub/issues/415
#           - https://github.com/PyGithub/PyGithub/pull/820
#---------------------------------------------------------------------------
def check_row_quant_safety( paged_list, config_quant, log_msg, diagnostics, logger ):

    # init vars
    output_quant    = 0
    stripped_quant  = config_quant.strip()
    str_param_quant = str.lower( stripped_quant )


    # log and print message about which set of data we are checking rows for
    # e.g. "Checking row quant safety for issue data"
    log_and_print( log_msg, "INFO", logger )

    # Subprocess 1a
    if str_param_quant == "all" or int( config_quant ) > paged_list.totalCount:
        output_quant = int( paged_list.totalCount )

    # Subprocess 1b
    elif int( config_quant ) <= paged_list.totalCount:
        output_quant = int( config_quant )

    # Subprocess 1c
    else:
        log_and_print( "INVAL_ROW", "ERROR", logger )


    # print output quant for diagnostics
    if diagnostics == "true":
        print( NL_TAB + DIAG_MSG )
        print( TAB + TAB + "Rows of data to be retrieved: " + str( output_quant ))


    complete( logger )

    return output_quant




#---------------------------------------------------------------------------
# Name   : collate_py_lists
# Context: After collecting all the relevant data using the issue, PR, and
#          commit getter methods, we have three separate JSON files that
#          contain that respective data. It is useful for the CSV writing
#          stage for us to have all of that data in one place. This function
#          takes all of that data and writes it into one file, making sure
#          that the data is associated correctly ( such as appending PR and
#          commit info to appropriate, complementary issue info ).
#
# Process: 1) iterate through the metalist ( list of lists ) of issue info.
#             When the issue number of a given issue matches that of a given
#             PR:
#
#             a) switch isPR to 1, indicating that this issue is also a PR.
#               - Note: Concerning GitHub, all PRs are issues but not all
#                       issues are PRs
#             b) append the associated PR and commit list to that row of
#                issue info.
#               - Note: The consequence of this is that the index that contains
#                       an issue's associated PR or commit info has an entire
#                       list in it.
#
# Params : 1) Info_metalist
#           - type: tuple
#           - desc: contains Python lists of lists of relevant repo
#                   information. These groups of info are collatable
#                   because they discuss the same objects of inquiry
#
# Output : one Python list, with nested lists, containing collated repo info
# Notes  : none
# Docs   : none
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


    # Subprocess 1:
    while issue_index < issue_list_len:

        # reset vars
        isPR = 0

        # get issue and PR nums to line up values
        issue_num = issue_metalist[issue_index][0]
        pr_num    = pr_metalist[pr_index][0]

        if issue_num == pr_num:

            # Suprocess 1a:
            isPR = 1

            # Suprocess 1b:
            #   append entire lists to issue list:
            issue_metalist[issue_index].append( pr_metalist[pr_index] )
            issue_metalist[issue_index].append( commit_metalist[pr_index] )

            if pr_index < pr_list_len - 1 :
                pr_index += 1


        issue_metalist[issue_index].append( isPR )

        issue_index += 1


    return issue_metalist




#---------------------------------------------------------------------------
# Name   : complete
# Context: This program uses a good deal of logging and console printing to
#          inform the user about events inside of its operation. A common item
#          that this program logs and prints is a completion message. So as to
#          make the code look and read cleaner, this wrapper function provides
#          a means of logging and printing those completion messages in an
#          abbreviated format
#
# Process: call log_and_print with fixed input parameters
# Params : 1) logger
#           - type: Python Logger object
#           - desc: Used for logging operations
#           - docs: https://docs.python.org/3/howto/logging.html#loggers
#
# Output : logs and prints preconfigured completion messages
# Notes  : none
# Docs   : none
#---------------------------------------------------------------------------
def complete( logger ):

    log_and_print( "COMPLETE", "INFO", logger )




#---------------------------------------------------------------------------
# Name   : exe_menu
# Context: This method is executed in the driver, after the configuration
#          information has been collected from the cfg file provided at the
#          commandline. Its purpose is to act as entrypoint for the user,
#          where they can choose what operation to perform.
#
# Process: There are several paths that this function can take, depending on
#          the user's choice:
#
#          1) gather user choice for program operation
#          2) if user chose 1, 2, or 5, gather paginated lists of data and
#             execute:
#             a) choice 1: get issue data JSON
#             b) choice 2: get PR and commit data JSON
#             c) choice 5: get both
#
#          3) if user chose 3 or 5, create cumulative JSON from three prior
#             JSON lists
#
#          4) if user chose 4 or 5, prompt user for choice of CSV output
#             creation
#
#             a) if user chooses 1 or 3, create "PR" csv output
#             b) if user chooses 2 or 3, create "Commit" csv output
#
# Params : 1) conf_list
#           - type: Python list
#           - desc: contains list of settings from the configuration file arg
#
#          2) session
#           - type: GitHub object
#           - desc: acts as the user's connection to GitHub REST API
#           - docs: https://pygithub.readthedocs.io/en/latest/github.html
#
#          3) logger
#           - type: Python Logger object
#           - desc: Used for logging operations
#           - docs: https://docs.python.org/3/howto/logging.html#loggers
#
# Output : various, see Process section above
# Notes  : none
# Docs   : 1) Python sets used for str parity conditionals, e.g.
#
#               "if op_choice in { '1', '2', '5' }:"
#
#           - https://www.w3schools.com/python/python_sets.asp
#---------------------------------------------------------------------------
def exe_menu( conf_list, session, logger ):

    # gather config values
    repo_str             = conf_list[1]
    diagnostics_flag     = conf_list[6]

    master_json_filename = conf_list[11]

    pr_csv_filename      = conf_list[12]
    commit_csv_filename  = conf_list[13]

    pr_separator         = conf_list[14]
    commit_separator     = conf_list[15]

    # init other vars
    conf_tuple = tuple( conf_list )
    csv_choice = '3'


    # begin output
    log_header = HEADER %( conf_tuple )

    if diagnostics_flag == "true":
        print( NL + DIAG_MSG + NL + log_header )


    logger.info( log_header )

    # subprocess 1
    op_choice = input( PROG_INTRO )

    # subprocess 2
    if op_choice in { '1', '2', '5' }:

        log_and_print( "PROG_START", "INFO", logger )

        paged_metalist = get_paginated_lists( session, repo_str, logger, op_choice )

        issue_paged_list, pr_paged_list = paged_metalist

        # subprocess 2a
        if op_choice in { '1', '5' }:
            get_list_json( conf_list, session, logger, "ISSUE", issue_paged_list )


        # subprocess 2b
        if op_choice in { '2', '5' }:
            get_list_json( conf_list, session, logger, "PR", pr_paged_list )


    # subprocess 3
    if op_choice in { '3', '5' }:

        if op_choice == '3':
            log_and_print( "PROG_START", "INFO", logger )


        get_list_json( conf_list, session, logger, "ALL", None )


    # subprocess 4
    if op_choice in { '4', '5' }:

        if op_choice == '4':
            log_and_print( "PROG_START", "INFO", logger )

            csv_choice = input( CSV_PROMPT )


        # read master JSON list content out of file
        master_info_list = read_json( master_json_filename, "R_JSON_ALL", logger )

        # subprocess 4a
        if csv_choice in { "1", "3" }:
            write_csv( master_info_list, pr_csv_filename,
                       pr_separator, "pr", logger )


        # subprocess 4b
        if csv_choice in { "2", "3" }:
            write_csv( master_info_list, commit_csv_filename,
                       commit_separator, "commit", logger )




#---------------------------------------------------------------------------
# Name   : filter_commits
# Context: After collecting PR and commit info ( after selecting choice 2 or 3
#          at the menu ), the program will need to filter the commits before
#          the commit info is useful to the pipeline. The pipeline, as of
#          right now, requires commits that are a part of a merged PR and have
#          changed files attached to them. If a PR is not merged, it is
#          excluded from the PR data list. If a PR has no commits, there is no
#          data for commits associated with that PR. If the commits have no
#          files changed, they are also not appended to the list of commit
#          data. This function is responsible for creating the list of commits
#          that the parent function, get_commit_info, will derive specific
#          data from, such as the files that were changed in that commit. It
#          also creates a set of strings, later printed to the log, that
#          detail all of the files that were excluded from the commit list and
#          why they were ommitted.
#
# Process: 1) loop through metalist of PR nums and associated paged lists of
#             commits. These items are stored as lists in a list ( metalist ).
#
#             A) attempt to retrieve data from paged list of commits.
#
#                1) retrieve the two pieces of data that are stored in the
#                   lists stored in every index of the in list ( being the PR
#                   number of the PR associated with the paginated list of
#                   commits and the paginated list of commits itself ).
#
#                2) retrieve the length of the paginated list of commits.
#                   len() does not work as of the time of writing, we must use
#                   the totalCount attribute
#
#                3) test if this PR has commits. If not, we do not want to
#                   include it in the out list of commit objects and will
#                   instead put it in a list to be displayed in the log that
#                   is created for this operation.
#
#                   a) As of writing, the project is interested in the last
#                      commit in the set of commits for a PR. We get this by
#                      subtracting one from the total length of the list.
#
#                   b) TODO:
#
#             B) In the case that we are rate limited, we sleep until we can
#                make calls again ( see the user-defined sleep function for
#                more info ).
#
#             C) otherwise, append the useful gathered data to an out list and
#                increment the index.
# Params :
# Output :
# Notes  :
# Docs   :
#---------------------------------------------------------------------------
def filter_commits( session, commit_py_metalist, logger ):

    index = 0

    commit_info_list       = []
    no_commit_str          = NL_TAB + "Pull requsts with no commits:"
    no_changed_file_str    = NL_TAB + "Commits with no changed files:"

    commit_py_metalist_len = len( commit_py_metalist )


    log_and_print( "F_COMMIT", "INFO", logger )

    # subprocess 1
    while index < commit_py_metalist_len:

        # reset vars
        most_recent_commit = NAN

        # subprocess 1A
        try:
            # subprocess 1A1
            cur_commit_pr_num     = commit_py_metalist[index][0]
            cur_commit_paged_list = commit_py_metalist[index][1]

            # subprocess 1A2
            num_of_commits = cur_commit_paged_list.totalCount

            # subprocess 1A3
            if num_of_commits > 0:

                # subprocess 1A3a
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

        # subprocess b
        except github.RateLimitExceededException:
            print()
            sleep( session, "F_MORE_COMMIT", logger )

        # subprocess c
        else:
            commit_info_list.append( most_recent_commit )

            print_rem_calls( session )

            index += 1


    diagnostics_lists = no_commit_str, no_changed_file_str

    complete( logger )


    return commit_info_list, diagnostics_lists




#---------------------------------------------------------------------------
# Name   : get_CLI_args
# Context: This program receives a group of settings from a text file in the
#          filesystem. This function is responsible for reading in the name of
#          that file and returning it to the driver function, from which this
#          function is called.
#
# Process: adds the ability to process commandline args and a grouping
#          of mutually exclusive args, collects and processes the args,
#          and returns them to the user
#
# Params : none
# Output : 1) config_filename
#             - type: str
#             - desc: name of config file
#
# Notes  : none
# Docs   : 1) argparse (library)
#             - link: https://docs.python.org/3/library/argparse.html
#---------------------------------------------------------------------------
def get_CLI_args():

    # establish positional argument capability
    arg_parser = argparse.ArgumentParser( description="OSL Repo mining script" )

    # add repo input CLI arg
    arg_parser.add_argument( 'config_file', type=str, help="config file name" )

    # retrieve positional arguments
    config_filename = arg_parser.parse_args().config_file


    return config_filename




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
    index                  = 0
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

        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_COMMIT", logger )

        else:
            # append list of collected commit info to metalist
            commit_metalist.append( commit_info_list )

            # print remaining calls per hour
            print_rem_calls( session )

            index += 1


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
                                         "V_ROW_#_ISSUE", diagnostics, logger )

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




# TODO:
# Merge this annotation into get_list_json below
#---------------------------------------------------------------------------
# Name   : create_master_json
# Context: After gathering data from whatever repo is passed into the program
#          and storing that data in Python lists, the data will be written to
#          three separate JSON files for storage ( for more info on that and
#          why that route was taken, please see the instruction txt file ).
#          Those lists are very useful for a few reasons but, for writing CSV
#          outputs ( the purpose of this program ), they are more useful
#          collated into one list. This function bundles the functionality
#          needed to accomplish that into one place.
#
# Process: 1) read repo info from the three files which store them into lists
#          2) send list of those lists into collation function
#          3) write collated list of repo info to CSV
#
# Params : 1) json_file_list
#           - type: Python list
#           - desc: contains filepaths to JSON lists of repo info
#
#          2) logger
#           - type: Python Logger object
#           - desc: Used for logging operations
#           - docs: https://docs.python.org/3/howto/logging.html#loggers
#
# Output : CSV output is written into file
# Notes  : none
# Docs   : none
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
# Name   :
# Context:
# Process:
# Params :
# Output :
# Notes  :
# Docs   :
#---------------------------------------------------------------------------
def get_list_json( cfg_list, session, logger, list_type, data_list ):

    # gather ecumenical config values
    row_quant        = cfg_list[3]
    diag_flag        = cfg_list[6]
    issue_json_file  = cfg_list[8]
    pr_json_file     = cfg_list[9]
    commit_json_file = cfg_list[10]


    if list_type == "ISSUE":
        issue_metalist = get_issue_info( session, data_list, row_quant,
                                         diag_flag, logger )

        write_json( issue_metalist, issue_json_file, "W_JSON_ISSUE", logger )


    elif list_type == "PR":
        # get metalist of pr information and commit info paginated list
        #  TODO: put this VV in Context
        #   We get the commit paginated lists here because it allows us
        #   to segment each group of commits into their own lists. It
        #   is possible to retrieve a monolithic list of commits from
        #   the github object but they would not be broken up by PR
        list_tuple = get_PR_info( session, data_list, row_quant, diag_flag,
                                  logger )

        pr_metalist, commit_metalist, unmerged_pr_str = list_tuple

        write_json( pr_metalist, pr_json_file, "W_JSON_PR", logger )

        # log issue diagnostic information
        logger.info( NL + "[Diagnostics]:" + NL + unmerged_pr_str )

        # PR and commit lists must be created together
        get_list_json( cfg_list, session, logger, "COMMIT", commit_metalist )


    elif list_type == "COMMIT":

        # get commit information
        commit_metalist, diag_strs = get_commit_info( session, data_list, logger )

        write_json( commit_metalist, commit_json_file, "W_JSON_COMMIT", logger )

        # log commit diagnostic information
        diag_strs = NL + diag_strs[0] + NL + diag_strs[1]

        logger.info( NL + "[Diagnostics]:" + diag_strs )


    # subprocess 4
    elif list_type == "ALL":
        master_json_filename = cfg_list[11]

        # Subprocess 4a:
        issue_info_list  = read_json( issue_json_file, "R_JSON_ISSUE", logger )
        pr_info_list     = read_json( pr_json_file, "R_JSON_PR", logger )
        commit_info_list = read_json( commit_json_file, "R_JSON_COMMIT", logger )

        # create list of python lists for collation function
        info_metalist = [issue_info_list, pr_info_list, commit_info_list]

        # Subprocess 4b:
        log_and_print( "COLLATE", "INFO", logger )
        collated_list = collate_py_lists( info_metalist )
        complete( logger )

        # Subprocess 4c:
        write_json( collated_list, master_json_filename, "W_JSON_ALL", logger )




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
def get_paginated_lists( session, repo_str, logger, op_choice ):

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


            if op_choice in { '1', '5' }:

                log_and_print( "G_PAGED_ISSUES", "INFO", logger )

                issues_list = repo_obj.get_issues( direction='asc',
                                                    sort='created',
                                                    state='closed' )

                print_rem_calls( session )

                complete( logger )


            if op_choice in { '2', '5' }:

                log_and_print( "G_PAGED_PR", "INFO", logger )

                pr_list = repo_obj.get_pulls( direction='asc',
                                              sort='created', state='closed' )

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
    unmerged_pr_str = NL_TAB + "Non-merged pull requests:"

    # diagnostics strings
    commit_list_len_diag = "        Length of commits list: "
    pr_list_len_diag     = "        Length of pr list     : "
    pr_num_diag          = "\n\n        PR num                : "


    safe_quant = check_row_quant_safety( pr_paged_list, row_quant, "V_ROW_#_PR",
                                         diagnostics, logger )

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
                        pr_body_str = pr_body_str.replace( '\r', '' )
                        pr_body_str = pr_body_str.replace( '\n\r', '' )


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

                    # create tuple of the cur pr number and commits
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
                        print( commit_list_len_diag + commit_list_len + '/' + row_quant_str )


                    print_rem_calls( session )

                    index += 1


            else:
                unmerged_pr_str += NL_TAB + TAB + pr_num_str
                index += 1


        except github.RateLimitExceededException:
            print()
            sleep( session, "G_MORE_PR", logger )


    complete( logger )

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
    Non-fatal:
        Invalid personal access token!
        Please see https://github.com/settings/tokens
        to create a token with \"repo\" permissions!
        Continuing without authentification...""",

            "INVAL_ROW"     : NL_TAB + "row_quant config value is invalid!",
            "NO_AUTH"       : """
    Non-fatal:
        Authorization file not found!
        Continuing without authentification...""",

            "R_CFG_DONE"    : NL_TAB + "Read configuration and initialize logging...",
            "R_JSON_ALL"    : reader + "collated data JSON...",
            "R_JSON_COMMIT" : reader + "commit data JSON...",
            "R_JSON_ISSUE"  : reader + "issue data JSON...",
            "R_JSON_PR"     : reader + "pull request data JSON...",
            "SLEEP"         : NL_TAB + "Rate Limit imposed. Sleeping...",
            "SUCCESS"       : " Success! ",
            "V_AUTH"        : NL_TAB + "Validating user authentification...",
            "V_ROW_#_ISSUE" : NL_TAB + "Validating row quantity config for issue data collection...",
            "V_ROW_#_PR"    : NL_TAB + "Validating row quantity config for pull request data collection...",
            "W_CSV_COMMIT"  : writer + "\"commit\" type CSV...",
            "W_CSV_PR"      : writer + "\"PR\" type CSV...",
            "W_JSON_ALL"    : writer + "master list of data to JSON...",
            "W_JSON_COMMIT" : writer + "list of commit data to JSON...",
            "W_JSON_ISSUE"  : writer + "list of issue data to JSON...",
            "W_JSON_PR"     : writer + "list of PR data to JSON...",
            "PROG_START"    : "\n Attempting program start... ",
            }


    out_msg = str_dict[msg_format]

    if log_type == "INFO":
        logger.info( out_msg )

        if msg_format not in { "COMPLETE", "PROG_START", "SUCCESS" } :
            out_msg = INFO_MSG + out_msg

        else:
            out_msg = SUCCESS_MSG %( out_msg )

            if msg_format == "COMPLETE":
                out_msg = NL_TAB + TAB + out_msg + NL

            elif msg_format == "SUCCESS":
                out_msg = NL + NL + out_msg


    elif log_type == "ERROR":
        logger.error( out_msg )
        out_msg = NL_TAB +  ERR_MSG + out_msg

    elif log_type == "EXCEPT":
        logger.exception( out_msg )

        if out_msg != "SLEEP":
            out_msg = EXCEPT_MSG + out_msg


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
# Function name:
# Process      :
# Parameters   :
# Output       :
# Notes        :
# Other Docs   :
#---------------------------------------------------------------------------
def read_auth( authfile_name, logger ):

    try:
        authfile_obj = open( authfile_name, 'r' )

    except FileNotFoundError:
        log_and_print( "NO_AUTH", "ERROR", logger )

        auth_token = "none"

    else:
        # read contents out of auth file object
        # this should be one line with a personal accss token ( PAT )
        authinfo_line = authfile_obj.readline()

        # remove newline chars from PAT
        newLine_stripped_token = authinfo_line.strip( '\n' )

        # remove leading and trailing whitespaces from PAT
        auth_token = newLine_stripped_token.strip()

        authfile_obj.close()


    return auth_token




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
        conffile_obj = open( config_file_name, 'r' )

    except FileNotFoundError:
        print( "\nConfiguration file not found!" )

    else:
        # read contents out of file object
        confinfo_list = conffile_obj.readlines()

        # if a line is not an empty line or does not begin with a '-', we want
        # to strip the line of newline chars and update the prior list
        confinfo_list = [line.strip( '\n' ) for line in confinfo_list
                         if line[0] != '-' if line != '\n']

        for line in confinfo_list:

            stripped_line = line.replace( " ", '' )

            if stripped_line != '':

                # split line at assignment operator
                conf_sublist = stripped_line.split( "=" )

                conf_line = conf_sublist[1]

                conf_list.append( conf_line )


        conffile_obj.close()


    # Total config length    : 16
    # list of config values ------
    #   config file name     : 0
    #   repo name str        : 1
    #   auth file name       : 2
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
    #   pr_separator         : 14
    #   commit_separator     : 15

    if len( conf_list ) == 16:

        diagnostics_flag = conf_list[6] = str.lower( conf_list[6] )

        if diagnostics_flag == "true":
            print( NL + BKYEL + " [Diagnostics enabled] " + TXTRST )
            print( NL + DIAG_MSG + NL_TAB + "Configuration is correct length!" )


        return conf_list

    else:
        print( NL + ERR_MSG )
        print( CONF_ERR )

        for item in conf_list:
            print( TAB + item )


        print( '\n' )




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
# Function name:
# Process      :
# Parameters   :
# Output       :
# Notes        :
# Other Docs   :
#---------------------------------------------------------------------------
def sleep( session, msg_format, logger ):

    # print that we are sleeping
    log_and_print( "SLEEP", "EXCEPT", logger )

    # get the amount of time until our call amount is reset
    sleep_time = get_limit_info( session, "reset" )

    # sleep for that amount of time
    timer( sleep_time )

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
def verify_auth( authfile_name, diagnostics, logger ):

    log_and_print( "V_AUTH", "INFO", logger )

    auth_token = read_auth( authfile_name, logger )

    if str.lower( auth_token ) == "none":
        session    = github.Github( timeout=100, retry=100 )

    # attempt to verify
    else:
        session    = github.Github( auth_token, timeout=100, retry=100 )

        try:
            session.get_user().name

        except github.BadCredentialsException:
            log_and_print( "INVAL_TOKEN", "EXCEPT", logger )
            session    = github.Github( timeout=100, retry=100 )

        except github.RateLimitExceededException:
            sleep( session, None, logger )

        else:
            if diagnostics == "true":
                print( NL_TAB + DIAG_MSG + NL_TAB + TAB + "Personal Access Token valid!" )


    complete( logger )

    return session



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
#                1) topic: converting str of esc chars to esc chars
#                   - link: https://stackoverflow.com/questions/4020539/process-escape-sequences-in-a-string-in-python/4020824#4020824
#---------------------------------------------------------------------------
def write_csv( master_info_list, out_filename, separator, output_type, logger ):

    # init other vars
    list_index      = 0
    master_list_len = len( master_info_list )

    col_names   = ["Issue_Number", "Issue_Title", "Issue_Author_Name",
                   "Issue_Author_Login","Issue_Closed_Date", "Issue_Body",
                   "Issue_Comments", "PR_Title", "PR_Author_Name",
                   "PR_Author_Login", "PR_Closed_Date", "PR_Body",
                   "PR_Comments", "Commit_Author_Name",
                   "Commit_Date", "Commit_Message", "isPR"]

    log_msg     = "W_CSV_PR"

    if output_type == "commit":
        col_names = ["Issue_Num", "Author_Login", "File_Name",
                      "Patch_Text", "Commit_Message", "Commit_Title" ]

        log_msg = "W_CSV_COMMIT"


    log_and_print( log_msg, "INFO", logger )

    verify_dirs( out_filename )

    if '\\' in separator:

        # see "Other Docs" topic 1)
        str_bytes_obj = bytes( separator, "utf-8" )
        separator     = str_bytes_obj.decode( "unicode_escape" )


    with open( out_filename, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL,
                             delimiter=separator, quotechar='\"',
                             escapechar='\\' )

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
            # Use this list to choose what data to include in your output
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

                writer.writerow( output_row )


            # as the loop moves through the data, we want to exclude from this
            # specific output type any issues that are not PRs. During the
            # filtering process, we make sure that the PRs in the list of data
            # that comes into this function are all merged and that the
            # commits associated with those PRs all have files changed
            elif output_type == "commit":
                if isPR == 1 and len( commit_file_list ) > 0:

                    # Order: Issue_Num, Author_Login, File_Name,
                    #        Patch_Text, Commit_Message, Commit_Title

                    output_row = [issue_num, issue_author_name,
                                  commit_file_list, commit_patch_text,
                                  pr_body, issue_title]

                    writer.writerow( output_row )


            list_index += 1


    complete( logger )




#---------------------------------------------------------------------------
# Function name: write_issue_json
# Process      :
# Parameters   :
# Output       :
# Notes        :
# Other Docs   :
#---------------------------------------------------------------------------
def write_json( info_metalist, json_filename, msg_format, logger ):

    log_and_print( msg_format, "INFO", logger )

    verify_dirs( json_filename )

    json_io( json_filename, 'w', info_metalist )

    complete( logger )




if __name__ == '__main__':
    main()
