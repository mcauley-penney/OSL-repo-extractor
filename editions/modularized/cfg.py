#--------------------------------------------------------------------------- 
# Author : Jacob Penney 
# Purpose: 
# Process: 
# Notes  : 
#--------------------------------------------------------------------------- 

# constants
DASHES= "-----------------------------------------------------------"
BKBLU     = "\033[1;38;5;15;48;2;0;111;184m"  
BKGRN     = "\033[1;38;5;0;48;2;16;185;129m"  
BKRED     = "\033[1;38;5;0;48;2;240;71;71m"  
BKYEL     = "\033[1;38;5;0;48;2;251;191;36m"  
NAN       = "NaN"
NL        = '\n'
TXTRST    = "\033[0;0m" 
TAB       = "    "
TIME_FRMT = "%D, %I:%M:%S %p"

LOG_BAR     = DASHES + DASHES
DIAG_MSG    = TAB + BKYEL +" [Diagnostics]: " + TXTRST + ' ' 
NL_TAB      = NL + TAB
INFO_MSG    = NL_TAB + BKBLU + " Info: " + TXTRST
ERR_MSG     = NL_TAB + BKRED + " Error: " + TXTRST
EXCEPT_MSG  = NL_TAB + BKRED + " Exception: " + TXTRST 
