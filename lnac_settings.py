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

    i_tx_data[0] = 0;
    i_tx_data[1] = 3; 
    
    
    
    status = bridge_init()
    if(status != 0):
        print("Device not found! Sorry")
        exit()
    
#    while program_run == 1:
#        if(kbhit()):
#            program_run = 0
    # Send data to device
    Uniprot_config_TX_packet( 2 )
    Uniprot_config_RX_packet( 44 )
    Uniprot_USB_tx_data( i_tx_data )
        
        
    Uniprot_USB_rx_data()
    
    #raw_input("Answer to AVR")
    
    Uniprot_USB_tx_command('N')
    
    Uniprot_USB_rx_data()
    
    Uniprot_USB_tx_command('A')
        
#    device = usb_open_device(0x03EB, 0x204F)
#   if(device == 404):
#        print("Dev not found")
#    print(device)
    
    # When program_run will be not equal 1 -> jump out of the while

    bridge_close()
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
    
    exit()


