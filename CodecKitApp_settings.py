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

import struct


##
# @brief Main function
if __name__ == '__main__':
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL
    
    print("[LNAC settings] Alive!")
    
    cfgPars = BridgeConfigParser()
    
    filename="test.cfg"
    
    cfgPars.write_setting_to_cfg_file(filename)
    #cfgPars.read_setting_from_file(filename)
    
    
    exit()
    
    
    status = "???"
    # Bridge init
    try:
        bridge = Bridge()
    except BridgeException_Device_not_found as e:
        logger.error("[Bridge]" + str(e))
        print("Exiting....")
        exit()
        
        
    print (" INIT OK\n\n\n\n")
    
    # Print all metadata
    for i in range(bridge.get_max_Device_ID() +1):
        print("Device ID:")
        print(bridge.device_metadata[i])
    
    DID = 1
    CMD = 14
    new_val = 1
    
    print(bridge.get_all_settings[DID][CMD].out_value)
    
    
    status = bridge.set_setting_to_device(DID, CMD, new_val)
    
    print(status)
    
    print(bridge.get_all_settings[DID][CMD].out_value)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    try:
        bridge.close()
    except:
        pass
    print("[LNAC settings] Bye")
    
    exit()


#    for i in i_buffer_rx:
#        print("RXD {0} | {1} | {2}".format(hex(i), str(unichr(i)), i ))

