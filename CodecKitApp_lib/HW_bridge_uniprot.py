#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
#
# @brief: Bridge between universal protocol and hardware
#
# Functions for higher layer:
#  bridge_init() - must be called first
#  bridge_close() - should be called when no communication is needed
#                    (at the end of program)
#
#  bridge_get_number_of_devices() - should be called only when number of
#                                   devices is changed. Function bridge_init()
#                                   call this function, so at the begin bridge
#                                   know how many devices are under control
#
# @author: Martin Stejskal
#

from uniprot import *
from compiler.ast import Print



# @brief: "Constants"
# @{
# options: debug, release
const_HW_BRIDGE_uniprot_VERSION = "release"
#const_HW_BRIDGE_uniprot_VERSION = "debug"

const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT = 10

# In some cases should be defined maximum size of RX buffer
const_HW_BRIDGE_UNIPROT_MAX_RX_BUFFER_BYTES = 65530 

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
# @brief Class for structures
# @{

# @brief Dynamic structure for metadata. Default should be invalid values
class BRIDGE_METADATA:
    def __init__(self):
        i_Device_ID = -1
        i_MAX_CMD_ID = -1
        i_serial = -1
        s_descriptor = ""


class RES_CODE:
    GD_SUCCESS =                   0
    GD_FAIL =                      1
    GD_INCORRECT_PARAMETER =       2
    GD_INCORRECT_CMD_ID =          3
    GD_CMD_ID_NOT_EQUAL_IN_FLASH = 4
    GD_INCORRECT_DEVICE_ID =       5
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


"""
class Bridge():
    
    
    def __init__(self):
        # Tady prekopiruj Bridge_init()
    
    def get_number_of_devices(self):
        
"""


##
# @brief Global variables
# @{

##
# @brief Number of detected devices (-1 -> error -> so far none)
i_num_of_devices = -1;
# @}

#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#

##
# @brief: Print message only if version is debug
def print_if_debug_bridge( string ):
    global const_HW_BRIDGE_uniprot_VERSION
    
    if const_HW_BRIDGE_uniprot_VERSION == "debug":
        print( string )

#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#

##
# @brief: Try to get number of devices connected to target
# 
# @return: Number of detected devices connected to target
def bridge_get_number_of_devices():
    global i_num_of_devices
    
    global const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_NUM_OF_DEV
    global const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT
    
    const_func_name = "Get number of devices: "
    
    # Fill TX buffer
    i_tx_buffer = [0x00]*2
      # Device ID - ALWAYS MUST BE 0 !!!
    i_tx_buffer[0] = 0x00;  
      # Bridge command (request number)
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
            # Try to get status (but mainly send data/request)
            status = Uniprot_USB_tx_data( i_tx_buffer )
            
        except UniprotException_Device_not_found as e:
            print_if_debug_bridge(str(e))
            raise BridgeException_Device_not_found("[Uniprot TX data] "
                                                    + str(e))
        
        except UniprotException_NACK_fail as e:
            print_if_debug_bridge(str(e))
            raise BridgeException_NACK_fail("[Uniprot TX data]" + str(e))
        
        except UniprotException_RX_buffer_overflow as e:
            print_if_debug_bridge(str(e))
            raise BridgeException_Device_RX_buffer_overflow("[Uniprot TX data]"
                                                             + str(e))
        
        except UniprotException_Reset_success as e:
            print_if_debug_bridge(str(e))
            # Send data once again
            i_retry_cnt = i_retry_cnt + 1
            if(i_retry_cnt > const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT):
                print_if_debug_bridge("[bridge_get_number_of_devices] Retry"
                                      " limit reached")
                raise BridgeException_Reset_fail(" Reset retry count reach"
                                                 "maximum (TX data).")
        else:
            # If Uniprot_USB_tx_data end as expected -> no exception -> break 
            break
        
        
    print_if_debug_bridge("Get number of devices status: " + status)
    
    
    # Reset counter
    i_retry_cnt = 0
    
    # When all OK, then RX data (expect from AVR)
    while(1):
        try:
            i_buffer_rx = Uniprot_USB_rx_data()
        except UniprotException_Device_not_found as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            raise BridgeException_Device_not_found("[Uniprot RX data]"
                                                    + str(e))
        except UniprotException_Reset_success as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            # Send data once again
            i_retry_cnt = i_retry_cnt + 1
            if(i_retry_cnt > const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT):
                print_if_debug_bridge("[bridge_get_number_of_devices] Retry"
                                      " limit reached")
                raise BridgeException_Reset_fail(" Reset retry count reach"
                                                 "maximum (RX data).")
        else:
            # If Uniprot_USB_rx_data end as expected -> no exception -> break
            break
    
    # Test if send Device ID is correct
    if(i_buffer_rx[0] != 0):
        # This should not happen. It is not big problem, but it is not standard
        # behaviour
        print("[bridge_get_number_of_devices] Warning: Device ID is not 0x00!")
    
    # Test if there is some problem on AVR side
    if(i_buffer_rx[1] == 0):
        # No problem, everything works
        
        i_num_of_devices = i_buffer_rx[2]
        # Send only number of devices (max. device index number)
        return i_buffer_rx[2]
    
    # Else exception - this never should happen
    raise BridgeException_Error("Error code from AVR is not 0, but it should"
                                " be!")

#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#

##
# @brief: Connect to the target device if possible
def bridge_init():
    try:
        Uniprot_init()
        bridge_get_number_of_devices()

    except UniprotException_Device_not_found as e:
        print_if_debug_bridge(str(e))
        raise BridgeException_Device_not_found("[Uniprot init] " + str(e))
        
        
    except BridgeException_Device_not_found as e:
        print_if_debug_bridge(str(e))
        raise UniprotException_Device_not_found("[Get num of dev] " + str(e))
        
    except BridgeException_Device_RX_buffer_overflow as e:
        print_if_debug_bridge(str(e))
        raise BridgeException_Device_RX_buffer_overflow("[Get num of dev] "
                                                         + str(e))
        
    except BridgeException_NACK_fail as e:
        print_if_debug_bridge(str(e))
        raise BridgeException_NACK_fail("[Get num of dev] " + str(e))
    
    except BridgeException_Reset_fail as e:
        print_if_debug_bridge(str(e))
        raise BridgeException_Reset_fail("[Get num of dev] " + str(e))
    
    """
    result = range(10)
    i = 0
    for xxx:
        result.append()
        """

def bridge_close():
    try:
        Uniprot_close()
        
    except UniprotException_Device_not_found as e:
        # Even if this exception occurs, program can re-initialize device
        # if needed
        print_if_debug_bridge(e)
        raise BridgeException_Device_not_found("[Uniprot close] " + str(e))


#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#

def bridge_get_metadata(i_Device_ID):
    # Global variable for number of devices.
    global i_num_of_devices
    
    global const_HW_BRIDGE_UNIPROT_MAX_RX_BUFFER_BYTES
    
    global const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_METADATA
    global const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT
    
    
    # Check if Device ID is valid
    if(i_Device_ID > i_num_of_devices):
        message = " Invalid Device ID. "
        if(i_num_of_devices < 0):
            message = message + "It looks that bridge was not initialized." +\
                " Please call function Uniprot_init() and check all exceptions"
        else:
            # It look that bridge was initialized, but Device ID is invalid
            message = message + "Maximum Device ID is " +\
                 str(i_num_of_devices) + " ."
        
        raise BridgeException_Error(message)
    
    
    
    # Fill TX buffer by zeros
    i_tx_buffer = [0x00]*2
      # Device ID
    i_tx_buffer[0] = i_Device_ID
      # Bridge command (request ID)
    i_tx_buffer[1] = const_HW_BRIDGE_UNIPROT_STATE_REQUEST_GET_METADATA
    
    
    
    # Configure TX packet
    Uniprot_config_TX_packet( 2 )
    
    # Configure RX packet
    Uniprot_config_RX_packet( const_HW_BRIDGE_UNIPROT_MAX_RX_BUFFER_BYTES )
    
    # Reset counter
    i_retry_cnt = 0
    
    while(1):
        try:
            # Try to send request
            status = Uniprot_USB_tx_data( i_tx_buffer )
            
        except UniprotException_Device_not_found as e:
            print_if_debug_bridge(str(e))
            raise BridgeException_Device_not_found("[Uniprot TX data] "
                                                    + str(e))
        
        except UniprotException_NACK_fail as e:
            print_if_debug_bridge(str(e))
            raise BridgeException_NACK_fail("[Uniprot TX data]" + str(e))
        
        except UniprotException_RX_buffer_overflow as e:
            print_if_debug_bridge(str(e))
            raise BridgeException_Device_RX_buffer_overflow("[Uniprot TX data]"
                                                             + str(e))
        
        except UniprotException_Reset_success as e:
            print_if_debug_bridge(str(e))
            # Send data once again
            i_retry_cnt = i_retry_cnt + 1
            if(i_retry_cnt > const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT):
                print_if_debug_bridge("[bridge_get_number_of_devices] Retry"
                                      " limit reached")
                raise BridgeException_Reset_fail(" Reset retry count reach"
                                                 "maximum (TX data).")
        else:
            # Else TX data without exception -> break while
            break
        
        
    print_if_debug_bridge("Get metadata status: " + status)
    
    # Reset counter
    i_retry_cnt = 0
    
    # RX data (metadata)
    while(1):
        try:
            i_buffer_rx = Uniprot_USB_rx_data()
            
        except UniprotException_Device_not_found as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            raise BridgeException_Device_not_found("[Uniprot RX data]"
                                                    + str(e))
        except UniprotException_Reset_success as e:
            print_if_debug_bridge("[bridge_get_number_of_devices]" + e)
            # Send data once again
            i_retry_cnt = i_retry_cnt + 1
            if(i_retry_cnt > const_HW_BRIDGE_UNIPROT_MAX_RETRY_CNT):
                print_if_debug_bridge("[bridge_get_number_of_devices] Retry"
                                      " limit reached")
                raise BridgeException_Reset_fail(" Reset retry count reach"
                                                 "maximum (RX data).")
        else:
            # Else no exception -> break while
            break
    
    # Test if send Device ID is same
    if(i_buffer_rx[0] != i_Device_ID):
        # This should not happen.
        message = " Got different Device ID (" + str(i_buffer_rx[0]) +\
            "), but expected " + str(i_Device_ID) + " . This is failure of"\
            "communication protocol."
        raise BridgeException_Error(message)
    
    # Test return code - never should happen, but...
    if(i_buffer_rx[1] != 0):
        print_if_debug_bridge("[bridge_get_metadata] Return code: " +
                               str(i_buffer_rx[1]))
        # This never happen. Only one thing that may fail is wrong Device ID,
        # but this is checked before request is send. It can fail only when
        # whole protocol fail -> developer should fix this
        message = "Device returned code: " + str(i_buffer_rx[1]) +\
             ". Please refer to source code what error code means."\
             " However this should not happen. It is seems that there is"\
             " some problem when transmitting or receiving data."
        raise BridgeException_Error(message)
    
    
    # Else all seems to be OK -> fill metadata structure
    rx_metadata = BRIDGE_METADATA()
    
    # Load Device ID
    rx_metadata.i_Device_ID = i_buffer_rx[0]
    
    # Metadata begin at index 2 (3rd byte)
    i_index = 2
    
    # Load MAX CMD ID
    rx_metadata.i_MAX_CMD_ID = (i_buffer_rx[i_index])<<8
    i_index = i_index+1
    rx_metadata.i_MAX_CMD_ID = rx_metadata.i_MAX_CMD_ID + i_buffer_rx[i_index]
    i_index = i_index+1
    
    # Load serial number
    rx_metadata.i_serial = i_buffer_rx[i_index]
    i_index = i_index+1
    
    # Clear descriptor
    rx_metadata.s_descriptor = ""
    
    # Load descriptor
    while(i_buffer_rx[i_index] != 0x00):
        # Add character to descriptor
        rx_metadata.s_descriptor = rx_metadata.s_descriptor + str(unichr(i_buffer_rx[i_index]))
        
        # Increase index
        i_index = i_index+1
    
    # return metadata as object
    
    return rx_metadata

#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#

def bridge_get_settings(i_Device_ID, i_CMD_ID):
    print("Complete function")
    exit()



