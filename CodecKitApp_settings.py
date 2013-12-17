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
    
    
    
    """
    i = 1082759578
    
    i = (66<<24) + (49<<16) + (50<<8) + (51);
    
    i = 0x4089999A
    i = 0xA9999804
    #i = 0x404e3233
    #i = "432.3"
    #i = struct.pack('f', -5.1)
    array = [0x00] * 4
    array[3] = i>>24 & 0xFF
    array[2] = (i>>16) & 0xFF
    array[1] = (i>>8) & 0xFF
    array[0] = i & 0xFF
    for i in range(4):
        print(array[i])
    
    test = unichr(array[0]) + unichr(array[1]) + unichr(array[2]) + unichr(array[3])
    print("\n Test variable:\n  "  + test)

    #test = struct.unpack('f', '\xdb\x0fI@')
    p = struct.unpack('f', "adke")
    print(p)
    p = struct.unpack('f', test)
    
    print(p)
    #test = "123V"
    
    #p = struct.unpack('f', test)
    
    
    #print(float(i) -1)
    #print(p)
    
    exit()
    """
    
    cfgPars = BridgeConfigParser()
    
    filename="test.cfg"
    
    cfgPars.write_setting_to_cfg_file(filename)
    
    
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