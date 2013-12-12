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

# Time operations
from time import sleep

# Keyboard events (only debug for now)
#from msvcrt import kbhit



##
# @brief Main function
if __name__ == '__main__':
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL
    
    print("[LNAC settings] Alive!")
    
    
    status = "???"
    """
    crc = 0
    crc = crc_xmodem_update(crc, 0x48)
    crc = crc_xmodem_update(crc, 0x0)
    crc = crc_xmodem_update(crc, 0x8)
    crc = crc_xmodem_update(crc, 0x44)
    crc = crc_xmodem_update(crc, 0x1)
    crc = crc_xmodem_update(crc, 0x2)
    crc = crc_xmodem_update(crc, 0x0)
    crc = crc_xmodem_update(crc, 0x2)
    crc = crc_xmodem_update(crc, 0x0)
    crc = crc_xmodem_update(crc, 0x0)
    crc = crc_xmodem_update(crc, 0x0)
    crc = crc_xmodem_update(crc, 0xF)
    crc = crc_xmodem_update(crc, 0x54)
    
    print(crc)
    crc2 = crc
    crc2 = crc_xmodem_update(crc2, crc>>8)
    crc2 = crc_xmodem_update(crc2, crc & 0xFF)
    
    print(crc2)
    exit()
    """
    
    """
    one = GET_SETTINGS_STRUCT()
    
    one = {}
    one[device_id] = []
    one[device_id].append(GET_SETTINGS_STRUCT())
    one[device_id+1] = GET_SETTINGS_STRUCT()
    
    one[0][setting_index].i_in_type
    
    arr2 = [[0 for x in range(4)] for x in range(7)]
    
    print(arr2)
    """
    
    
    
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