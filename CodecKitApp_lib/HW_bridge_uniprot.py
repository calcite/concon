#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
#
# @brief: Bridge between universal protocol and hardware
#
# 
#
# @author: Martin Stejskal
#

from uniprot import *
from compiler.ast import Print



# @brief: "Constants"
# @{
# options: debug, release
#const_HW_BRIDGE_uniprot_VERSION = "release"
const_HW_BRIDGE_uniprot_VERSION = "debug"

const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT = 10

# Following constants must be same as in firmware (HW_bridge_uniprot)
const_HW_BRIDGE_UNIPROT_STATE_WAITING_FOR_REQUEST = 0
const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_SETTINGS = 1
const_HW_BRIDGE_UNIPROT_STATE_REQUEST_SET_SETTINGS = 2
const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_METADATA = 3
const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_NUM_OF_DEV = 4
const_HW_BRIDGE_UNIPROT_STATE_SEND_ONLY_RETURN_CODE = 5
const_HW_BRIDGE_UNIPROT_STATE_SEND_RETURN_CODE_AND_METADATA = 6
const_HW_BRIDGE_UNIPROT_STATE_SEND_RETURN_CODE_AND_SETTING = 7
##
# @}


##
# @brief Class for exceptions
# @{
class BridgeException_Device_not_found(Exception):
    pass

class BridgeException_Device_reconnect(Exception):
    pass

class BridgeException_Device_RX_buffer_overflow(Exception):
    pass

class BridgeException_NACK_fail(Exception):
    pass

class BridgeException_Reset_fail(Exception):
    pass

class BridgeException_Error(Exception):
    pass
# @}



##
# @brief: Print message only if version is debug
def print_if_debug_bridge( string ):
    global const_HW_BRIDGE_uniprot_VERSION
    
    if const_HW_BRIDGE_uniprot_VERSION == "debug":
        print( string )




##
# @brief: Connect to the target device if possible
def bridge_init():
    try:
        Uniprot_init()

    except UniprotException_Device_not_found as e:
        print_if_debug_bridge(e)
        raise BridgeException_Device_not_found("[bridge_init] Device not found!")

def bridge_close():
    try:
        Uniprot_close()
        
    except UniprotException_Device_not_found as e:
        # Even if this exception occurs, program can re-initialize device
        # if needed
        print_if_debug_bridge(e)
        raise BridgeException_Device_not_found("[bridge_close] Device not found!")



##
# @brief: Try to get number of devices connected to target
# 
# @return:  
def bridge_get_number_of_devices():
    global const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_NUM_OF_DEV
    global const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT
    
    # Global variables from uniprot
    global const_UNI_RES_CODE_SUCCESS
    global const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW
    global const_UNI_RES_CODE_DEVICE_NOT_FOUND
    
    const_func_name = "Get number of devices: "
    
    # Fill TX buffer
    i_tx_buffer = [0x00]*2
      # Device ID - ALWAYS MUST BE 0 !!!
    i_tx_buffer[0] = 0x00;  
      # Request number
    i_tx_buffer[1] = const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_NUM_OF_DEV
    
    # Configure TX packet
    Uniprot_config_TX_packet( 2 )
    
    # Configure RX packet (expect 3B)
    Uniprot_config_RX_packet( 3 )
    
    
    # Reset counter
    i_retry_cnt = 0
    
    # TX command request
    while(1):
        try:
            # Try to get status (but mainly send data)
            status = Uniprot_USB_tx_data( i_tx_buffer )
            
        except UniprotException_Device_not_found as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            raise BridgeException_Device_not_found("Device not found. TX data")
        
        except UniprotException_NACK_fail as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            raise BridgeException_NACK_fail("NACK fail. Different protocol?")
        
        except UniprotException_RX_buffer_overflow as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            raise BridgeException_Device_RX_buffer_overflow("It looks like\
             device is out of RAM.\
             Program can not send even 2Bytes. This is fatal problem and can\
             not be solved by this program. Sorry :(")
        
        except UniprotException_Reset_success as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            # Send data once again
            i_retry_cnt = i_retry_cnt + 1
            if(i_retry_cnt > const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT):
                print_if_debug_bridge("[bridge_get_number_of_devices] Retry"
                                      " limit reached")
                raise BridgeException_Reset_fail("Reset retry count reach"
                                                 "maximum. TX data")
        
        # If Uniprot_USB_tx_data end as expected -> no exception -> break 
        break
        
        
    print_if_debug_bridge("Get number of devices: " + status)
    
    
    # Reset counter
    i_retry_cnt = 0
    
    # When all OK, then RX data (expect from AVR)
    while(1):
        try:
            i_buffer_rx = Uniprot_USB_rx_data()
        except UniprotException_Device_not_found as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            raise BridgeException_Device_not_found("Device not found. RX data")
        except UniprotException_Reset_success as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            # Send data once again
            i_retry_cnt = i_retry_cnt + 1
            if(i_retry_cnt > const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT):
                print_if_debug_bridge("[bridge_get_number_of_devices] Retry"
                                      " limit reached")
                raise BridgeException_Reset_fail("Reset retry count reach"
                                                 "maximum. RX data")
        # If Uniprot_USB_rx_data end as expected -> no exception -> break
        break
    
    # Test if there is some problem on AVR side
    if(i_buffer_rx[1] == 0):
        # No problem, everything works
        # Send only number of devices (max. device index number)
        return i_buffer_rx[2]
    
    # Else exception - this never should happen
    raise BridgeException_Error("Error code from AVR is not 0, but it have to!")













