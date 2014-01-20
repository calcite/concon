#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
# @brief Python script for communication with LN_AC-00
#
# This script is written for AT90USB1287, but it can be modified
#
# @author Martin Stejskal

##
# Libraries for log events
import logging
import logging.config

logger = logging.getLogger('root')

import re


# Universal protocol for embedded systems
from CodecKitApp_lib.HW_bridge_uniprot import *


from CodecKitApp_lib.bridge_config_parser import *

# Time operations
from time import sleep

##
# @brief Main function
if __name__ == '__main__':
    # "w" for create cfg file, else read from cfg file
    rw_flag="w"
    # Filename for cfg file
    filename="test.cfg"
    
    
    print("[LNAC settings] v0.1b Alive!")
    
    
    
    cfgPars = BridgeConfigParser()
    
    
    if(rw_flag == "w"):
      cfgPars.write_setting_to_cfg_file(filename)
    else:
      cfgPars.read_setting_from_file(filename,
                                     ignore_errors=False,
                                     try_fix_errors=True)
      cfgPars.write_setting_to_device()
    
    
    cfgPars.close_device()
    
    print("[LNAC settings] Bye")

