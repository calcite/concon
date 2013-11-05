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
from lnac_lib.HW_bridge_uniprot import *

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
    
    buff_size = 150
    
    i_tx_data = [0x00]*buff_size

    i_tx_data[0] = 1;   # Device ID
    i_tx_data[1] = 3;   # Command
    
    
    
    status = bridge_init()
    if(status != 0):
        exit()
    
#    while program_run == 1:
#        if(kbhit()):
#            program_run = 0
    # Send data to device
    Uniprot_config_TX_packet( 2 )
    Uniprot_config_RX_packet( 1024 )
    print("CMD result:")
    print(Uniprot_USB_tx_data( i_tx_data ) )    # Send command
    
    # When all OK, then RX data (expect from AVR)
    i_buffer_rx = Uniprot_USB_rx_data()
    
    
    for i in i_buffer_rx:
        print("RXD {0} | {1} | {2}".format(hex(i), str(unichr(i)), i ))
    
    #raw_input("Answer to AVR")
    
    print(",.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.,.")
        
    # When program_run will be not equal 1 -> jump out of the while

    bridge_close()
    print("[LNAC settings] Bye")
    
    exit()


