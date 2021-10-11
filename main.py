# Author: MP


import conf
import extractor


def main():

    # init cfg
    cfg = conf.cfg()

    print( cfg.auth )

    # init extractor
    gh_reader = extractor.extractor( cfg )






#---------------------------------------------------------------------------
# Name   :
# Context:
# Process:
# Params :
# Output :
# Notes  :
# Docs   :
#---------------------------------------------------------------------------
def test():
    pass




if __name__ == "__main__":
    main()

