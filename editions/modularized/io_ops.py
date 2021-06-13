#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 


from . import cfg
from . log_ops import complete, log_and_print
from . os_ops import verify_dirs
import csv
import json




#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
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


    while issue_index < issue_list_len:

        # reset vars
        isPR = 0

        # get issue and PR nums to line up values
        issue_num = issue_metalist[issue_index][0]
        pr_num    = pr_metalist[pr_index][0]                   

        if issue_num == pr_num:

            isPR = 1

            # append entire lists to issue list:
            #   this forces all PR and commit info into singular indices in the
            #   issue list
            issue_metalist[issue_index].append( pr_metalist[pr_index] )
            issue_metalist[issue_index].append( commit_metalist[pr_index] )

            if pr_index < pr_list_len - 1 :
                pr_index += 1 


        issue_metalist[issue_index].append( isPR )

        issue_index += 1


    return issue_metalist



#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def create_master_json( json_file_list, logger ):

    # unpack list of JSON file names to read
    issue_json_filename  = json_file_list[0]
    pr_json_filename     = json_file_list[1]
    commit_json_filename = json_file_list[2]
    master_json_filename = json_file_list[3]


    # read metalists out of JSON storage
    issue_info_list  = read_json( issue_json_filename, "R_JSON_ISSUE", logger )
    pr_info_list     = read_json( pr_json_filename, "R_JSON_PR", logger )
    commit_info_list = read_json( commit_json_filename, "R_JSON_COMMIT", logger )

    # get list of python lists
    info_metalist = [issue_info_list, pr_info_list, commit_info_list] 
    

    # put all data content into one list
    log_and_print( "COLLATE", "INFO", logger )
    collated_list = collate_py_lists( info_metalist )
    complete( logger )


    # write that list to JSON 
    write_json( collated_list, master_json_filename, "W_JSON_ALL", logger )




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
        with open( config_file_name, 'r' ) as conffile_obj: 

            # read contents out of file object
            confinfo_list = conffile_obj.readlines()

            confinfo_list = [line.strip( '\n' ) for line in confinfo_list
                             if line[0] != '-' if line != '\n']

            for line in confinfo_list:
                
                stripped_line = line.replace( " ", '' )

                if stripped_line != '':

                    # split line at assignment operator
                    conf_sublist = stripped_line.split( "=" )

                    conf_line = conf_sublist[1]

                    conf_list.append( conf_line )

        # get auth_file name
        auth_file_name = conf_list[2]


    except FileNotFoundError:
        print( "\nConfiguration file not found!" ) 


    # read auth file
    else:
        try:
            with open( auth_file_name, 'r' ) as authfile_obj:

                # read contents out of auth file object
                # this should be one line with a personal accss token ( PAT )
                authinfo_line = authfile_obj.readline()

                # remove newline chars from PAT
                newLine_stripped_token = authinfo_line.strip( '\n' )
                    
                # remove leading and trailing whitespaces from PAT
                space_stripped_token = newLine_stripped_token.strip()

                # place PAT at end of list
                conf_list.append( space_stripped_token )

        except FileNotFoundError:
            print( "\nAuthorization file not found!" ) 
            

    # Total config length    : 15
    # list of config values ------
    #   config file name     : 0 
    #   repo name str        : 1
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
    #   session              : 14 

    if len( conf_list ) == 15:

        diagnostics_flag = conf_list[6] = str.lower( conf_list[6] )

        if diagnostics_flag == "true":
                
            print( '\n' + cfg.BKYEL + "[Diagnostics enabled]" + cfg.TXTRST )
            print( '\n' + cfg.DIAG_MSG + "Configuration is correct length!" )

        return conf_list

    else:
        print( "\nIncorrect configuration! Please update your settings!\n" ) 




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
def write_commit_csv( master_info_list, out_file_name ):
    
    # init other vars
    commit_col_names = ["Author Login", "Committer login", "PR Number",
                        "SHA", "Commit Message", "file name",
                        "Patch text", "Additions", "Deletions",
                        "Status", "Changes"] 
    list_index       = 0
    pr_list_len = len( master_info_list )
    

    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        # write column labels
        writer.writerow( commit_col_names ) 

        # aggregate data lists into rows
        while list_index < pr_list_len:

            # master JSON row order
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

            cur_issue            = master_info_list[list_index]
            isPR                 = cur_issue[-1]

            if isPR == 1:

                issue_num          = cur_issue[0]
                issue_title        = cur_issue[1]
                issue_author       = cur_issue[2]
                issue_closed_date  = cur_issue[4]
                issue_body         = cur_issue[5]

                cur_commit         = master_info_list[list_index][8]
                commit_message     = cur_commit[1] 
                commit_file_list   = cur_commit[5]
                commit_patch_text  = cur_commit[6] 

                # need: "pr_num", "author", "title",
                #       "body","commit","file_name",
                #       "date_closed","text"
                

                # order:  Author_Login, Committer_login, PR_Number,     
                #         SHA, Commit_Message, File_name,               
                #         Patch_text, Additions, Deletions,             
                #         Status, Changes                               
                # ------------------------------------------------------------
                # output_row = [commit_author_name, commit_committer, issue_num,
                #               commit_SHA, commit_message, commit_file_list,
                #               commit_patch_text, commit_adds, commit_rms,
                #               commit_status, commit_changes] 

                output_row = [ issue_num, issue_author, issue_title,
                               issue_body, commit_message, commit_file_list,
                               issue_closed_date, commit_patch_text ] 

                if len( commit_file_list ) > 0:
                    print( "\nPR num: " + issue_num + "; issue title: " + issue_title )
                    print( "commit message: " + commit_message )

                    print( commit_file_list )
                
                    writer.writerow( output_row ) 





            list_index += 1
 



#--------------------------------------------------------------------------- 
# Function name: write_issue_json
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def write_json( info_metalist, json_filename, msg_format, logger, ):

    log_and_print( msg_format, "INFO", logger )

    verify_dirs( json_filename )

    json_io( json_filename, 'w', info_metalist )

    complete( logger )
 


#--------------------------------------------------------------------------- 
# Function name: 
# Process      : 
# Parameters   : 
# Output       : 
# Notes        : 
# Other Docs   : 
#--------------------------------------------------------------------------- 
def write_pr_csv( master_info_list, out_file_name ):

    # init other vars
    list_index    = 0
    master_list_len = len( master_info_list )
    pr_col_names   = ["Issue_Number", "Issue_Title", "Issue_Author_Name",      
                      "Issue_Author_Login","Issue_Closed_Date", "Issue_Body",  
                      "Issue_Comments", "PR_Title", "PR_Author_Name",          
                      "PR_Author_Login", "PR_Closed_Date", "PR_Body",          
                      "PR_Comments", "Commit_Author_Name",                     
                      "Commit_Date", "Commit_Message", "isPR"]                 


    with open( out_file_name, 'w', newline='', encoding="utf-8" ) as csvfile:

        # create writer object
        writer = csv.writer( csvfile, quoting=csv.QUOTE_MINIMAL, delimiter='\a',
                             quotechar='\"', escapechar='\\' )
          
        # write column labels
        writer.writerow( pr_col_names )

        while list_index < master_list_len:

            # reset vars
            pr_title        = cfg.NAN
            pr_author_name  = cfg.NAN
            pr_author_login = cfg.NAN
            pr_closed_date  = cfg.NAN
            pr_body         = cfg.NAN
            pr_comments     = cfg.NAN 

            commit_author_name = cfg.NAN
            commit_message     = cfg.NAN
            commit_date        = cfg.NAN  


            # row order
            #   issue info : 0-6
            #       0: issue_num,
            #       1: issue_title_str,
            #       2: issue_name_str, 
            #       3: issue_login_str,
            #       4: issue_closed_date, 
            #       5: issue_body_str,
            #       6: issue_comment_str, 

            #   pr info    : [7][0-6]
            #       7[0]: pr_num
            #       7[1]: pr_title
            #       7[2]: pr_author_name
            #       7[3]: pr_author_login
            #       7[4]: pr_closed_date
            #       7[5]: pr_body
            #       7[6]: pr_comments
            #
            #   commit info: [8][0-10]
            #       8[0]: commit_author_name, 
            #       8[1]: commit_message,
            #       8[2]: commit_date,  
            #       8[3]: commit_committer,
            #       8[4]: commit_SHA, 
            #       8[5]: commit_file_list, 
            #       8[6]: commit_patch_text,
            #       8[7]: commit_adds,
            #       8[8]: commit_removes,
            #       8[9]: quoted_commit_status_str,
            #       8[10]: commit_changes 
            #
            #   isPR       : -1 (last)



            
            # get issue info 
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

            list_index += 1 
