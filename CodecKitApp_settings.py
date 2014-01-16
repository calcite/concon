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

# Universal protocol for embedded systems
from CodecKitApp_lib.HW_bridge_uniprot import *


from CodecKitApp_lib.bridge_config_parser import *

# Time operations
from time import sleep

# Keyboard events (only debug for now)
#from msvcrt import kbhit


##
# @brief Main function
if __name__ == '__main__':
    
    print("[LNAC settings] Alive!")
    """
    
    exit()
    """
    cfgPars = BridgeConfigParser()
    
    filename="test.cfg"
    
    cfgPars.write_setting_to_cfg_file(filename)
    #cfgPars.read_setting_from_file(filename)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    try:
        bridge.close()
    except:
        pass
    print("[LNAC settings] Bye")
    
    exit()


#    for i in i_buffer_rx:
#        print("RXD {0} | {1} | {2}".format(hex(i), str(unichr(i)), i ))

