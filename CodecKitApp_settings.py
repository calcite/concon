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

class GET_SETTINGS_STRUCT:
        def __init__(self):
            self.in_type = -1
            self.in_min = -1
            self.in_max = -1
            self.out_type = -1
            self.out_min = -1
            self.out_max = -1
            self.out_value = -1
            self.descriptor = ""
        def __str__(self):
            return "Get settings>\n IN TYPE: {0}\n IN MIN: {1}\n IN MAX: \n"\
                "{2}\n OUT TYPE: {3}\n OUT MIN: {4}\n OUT MAX: {5}\n "\
                "OUT VALUE: {7}\n DESCRIPTOR: {8}\n<---------------------->"\
                .format(self.in_type,  self.in_min,  self.in_max,\
                        self.out_type, self.out_min, self.out_max,\
                        self.out_value, self.descriptor)

##
# @brief Main function
if __name__ == '__main__':
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL
    
    print("[LNAC settings] Alive!")
    
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
    
    
    print("\nMAX DID: " + str(bridge.get_max_Device_ID()) + "\n")
    
    # Print metadata
    print(bridge.device_metadata[0])
    print(bridge.device_metadata[1])
    
    
    
    
    
    
    
    
    
    
    
    
    try:
        bridge.close()
    except:
        pass
    print("[LNAC settings] Bye")
    
    exit()


#    for i in i_buffer_rx:
#        print("RXD {0} | {1} | {2}".format(hex(i), str(unichr(i)), i ))