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

# Keyboard events (only debug for now)
#from msvcrt import kbhit

import struct

##
# @brief Main function
if __name__ == '__main__':
    
    print("[LNAC settings] Alive!")
    
    """
    
    exit()
    """
    
    rw_flag="w"
    
    cfgPars = BridgeConfigParser()
    
    filename="test.cfg"
    
    if(rw_flag == "w"):
      cfgPars.write_setting_to_cfg_file(filename)
    else:
      cfgPars.read_setting_from_file(filename)
      cfgPars.write_setting_to_device()
    
    try:
        bridge.close()
    except:
        pass
    print("[LNAC settings] Bye")
    
    exit()



