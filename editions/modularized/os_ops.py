#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 

import os


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
