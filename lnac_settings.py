#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
# @brief Python script for communication with LN_AC-00
#
# This script is written for AT90USB1287, but it can be modified
#
# @author Martin Stejskal

# Use pyWinUSB library for python and use shortcut "hid"
import pywinusb.hid as hid

# Time operations
from time import sleep

# Keyboard events (only debug for now)
from msvcrt import kbhit


##
# @brief "Constants"
# @{
def const_version():
    # options: debug, release
    return "debug"

def const_vid():
    return 0x03EB

def const_pid():
    return 0x204F
##
# @}


##
# @brief Global variables
# @{

##
# @brief For data from device
# When receiving data from device it is called function, that fill this\n
# global variable
i_data_in = [0x00]*8

# @}

##
# @brief Print message only if version is debug
def print_if_debug( string ):
    if const_version() == "debug":
        print( string )




##
# @brief Send byte (8 bits) to device
#
# Example: tx_data_to_device( 0xAB )
def tx_data_to_device( data_8bit ):
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = const_vid(),
                                 product_id = const_pid()).get_devices()[0]
        print_if_debug("Device found")
        device.open()
        print_if_debug("Device opened")
        
        # Find OUT endpoint
        out_report = device.find_output_reports()[0]
        
        # Define buffer ; 9 = report size (8 bits) + 1 byte (report id)
        buffer= [0x00]*9        # Create and clear buffer
        buffer[0]=0x00          # report id
        
        print("+-------------------------------")
        for i in range(8):
            buffer[i+1] = data_8bit[i]
            print("| TX: {0}".format(hex(data_8bit[i])))
        
        # Send data in buffer
        out_report.set_raw_data(buffer)
        out_report.send()
        
        print_if_debug("Data send")
        
        # Close device
        device.close()
        print_if_debug("Device closed\n\n")
    except:
        # If not found -> exception 
        print("Device not found. Please make sure that device is connected")
        return 404









##
# @brief Callback function for "set_raw_data_handler"
def in_sample_handler(data):
    # Write data to global variable
    global i_data_in
    
    for i in range(8):
        # Write from index 1 -> in index 0 is report_id 
        i_data_in[i] = data[i+1]
    
    # Print number in hex if in debug mode
    if const_version() == "debug":
        print("+-------------------------------")
        for i in range(8):
            print("| RX: {0}".format(hex(data[i+1])))


##
# @brief Receive byte (8 bits) from device
#
# Example: data = rx_data_from_device()
def rx_data_from_device():
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = const_vid(),
                                     product_id = const_pid()).get_devices()[0]
        print_if_debug("Device found")
        device.open()
        print_if_debug("Device opened")
    except:
        # If not found -> exception 
        print("Device not found. Please make sure that device is connected")
        return 404

    # Set i_data_in[0] to higher value than 255 (must be higher then 8 bit
    # maximum)
    global i_data_in
    i_data_in[0] = 512
    
    #set custom raw data handler
    device.set_raw_data_handler(in_sample_handler)
    
    # And wait until valid number will be received
    print_if_debug("W8 4 data")
    while i_data_in[0] > 255:  # Wait for valid data
    #while not kbhit() and device.is_plugged():    # Wait until pressed key
        sleep(0.04)
            
    print_if_debug("RX done")
      
    # Close device
    device.close()
    
    print_if_debug("Device closed\n\n")

    return i_data_in


##
# @brief Main function
if __name__ == '__main__':
    # define temporary buffer 
    data = [0x00]*8;
    # Fill buffer with demo data
    data[0] = 0x10
    for i in range(7):
        data[i+1] = data[i] +1
        
    tx_data_to_device( data )
    
    data = rx_data_from_device();
    
    
    if const_version() == "debug":
        print("+-------------------------------\n Data in buffer")
        for i in range(8):
            print(hex(data[i]))

