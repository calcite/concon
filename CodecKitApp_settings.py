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

# REMOVE
from CodecKitApp_lib.crc16_xmodem import *

# Time operations
from time import sleep

##
# @brief Main function
if __name__ == '__main__':
    # "w" for create cfg file, else read from cfg file
    rw_flag="w"
    
    
    # Filename for cfg file
    if(rw_flag == "w"):
      # Create file
      filename="test2.cfg"
    else:
      # Read from file
      filename="test.cfg"
    
    
    
    
    
    print("[LNAC settings] v0.1b Alive!")
    
    
    
    # Initialize Bridge (also download all data from AVR)
    cfgPars = BridgeConfigParser()
    
    
    if(rw_flag == "w"):
      # Create config file
      cfgPars.write_setting_to_cfg_file(filename)
    else:
      # Or read from config file
      cfgPars.read_setting_from_file(filename,
                                     ignore_errors=False,
                                     try_fix_errors=True)
      # And send changes to device
      cfgPars.write_setting_to_device()
    
    
    
    
    
    
    cfgPars.close_device()
    
    print("[LNAC settings] Bye")

