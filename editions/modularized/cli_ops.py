#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 


from . import cfg 
import argparse


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
    config_file_name = arg_parser.parse_args().config_file


    return config_file_name 




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
