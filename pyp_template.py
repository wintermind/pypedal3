###############################################################################
# NAME: <your module name here>
# VERSION: <your version here> (<your date here>)
# AUTHOR: <your name here> (<your e-mail here>)
# LICENSE: <your license here>
###############################################################################
# FUNCTIONS:
#     <namess of your functions here>
###############################################################################

## @package pyp_template
# pyp_template provides a skeleton on which user-defined modules may be built.
##

# You need to import the logging module in any PyPedal extension you write if
# you want that extension to make use of the PyPedal logfile.
import logging

# All of the standard PyPedal modules are listed here.  You should only
# import the modules that you will use directly from your new module.  If you
# do not want to import a module listed below, put a '#' at the start of the
# line.
from PyPedal import pyp_db
from PyPedal import pyp_demog
from PyPedal import pyp_graphics
from PyPedal import pyp_io
from PyPedal import pyp_metrics
from PyPedal import pyp_network
from PyPedal import pyp_nrm
from PyPedal import pyp_reports
from PyPedal import pyp_snp
from PyPedal import pyp_utils

##
# yourFunctionName() <description of what function does>
# @param <parameter_name> <parameter description>
# @retval <description of returned value(s)
def yourFunctionName(pedobj):
    """
    yourFunctionName() <description of what function does>
    """
    try:
        # Do something here
        logging.info('pyp_template/yourFunctionName() did something that you should describe in this message.')
        # return a value/dictionary/etc.
    except:
        logging.error('pyp_template/yourFunctionName() encountered a problem that you should describe in this message.')
        return 0
