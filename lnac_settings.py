#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
# @brief Python script for communication with LN_AC-00
#
# This script is written for AT90USB1287, but it can be modified
#
# @author Martin Stejskal

# Universal protocol for embedded systems
from lnac_lib.lnac_bridge_uniprot import *

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
    
    # Scheduler
    program_run = 1
    
#    while program_run == 1:
#        if(kbhit()):
#            program_run = 0
    # Send data to device
    Uniprot_config_TX_packet( 0 );
    Uniprot_config_RX_packet( 3 );
    Uniprot_USB_tx_data( 0x00 );
        
        
        
        
    
    # When program_run will be not equal 1 -> jump out of the while
    print("[LNAC settings] Bye")
    
    """"
    # define temporary buffer 
    data = [0x00]*8;
    # Fill buffer with demo data
    data[0] = 0x48
    data[1] = 0x00
    data[2] = 0x00
    data[3] = 0x44
    data[4] = 0x54
        
    
    crc = 0    
    crc = crc_xmodem_update(crc, const_UNI_CHAR_HEADER)
    crc = crc_xmodem_update(crc, 0x00)
    crc = crc_xmodem_update(crc, 0x00)
    crc = crc_xmodem_update(crc, const_UNI_CHAR_DATA)
    crc = crc_xmodem_update(crc, const_UNI_CHAR_TAIL)
    
    data[5] = crc>>8
    data[6] = crc & 0xFF
    
    print(hex(crc))
    """

