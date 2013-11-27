#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
#
# @brief: Bridge between universal protocol and hardware
#
# Functions for higher layer:
#  # Do initialization
#  bridge = Bridge()    # Initialization and download metadata
#  
#  # Get number of max Device_ID (used index)
#  max_DID = bridge.get_max_Device_ID()
#
#  # Get downloaded metadata - if invalid Device ID is given, then return 404
#  # else return valid metadata
#  bridge.get_metadata(2)
#
#  bridge.close()  # should be called when no communication is needed
#                  # (at the end of program)
#
#
# @author: Martin Stejskal
#

from uniprot import *
from compiler.ast import Print




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



class Bridge():
    # @brief: "Constants"
    # @{
    # options: debug, release
    #VERSION = "release"
    VERSION = "debug"
    
    MAX_RETRY_CNT = 10
    
    # In some cases should be defined maximum size of RX buffer
    MAX_RX_BUFFER_BYTES = 65530
    
    # Following constants must be same as in firmware (HW_bridge_uniprot)
    STATE_WAITING_FOR_REQUEST = 0
    STATE_REQUEST_GET_SETTINGS = 1
    STATE_REQUEST_SET_SETTINGS = 2
    STATE_REQUEST_GET_METADATA = 3
    STATE_REQUEST_GET_NUM_OF_DEV = 4
    STATE_SEND_ONLY_RETURN_CODE = 5
    STATE_SEND_RETURN_CODE_AND_METADATA = 6
    STATE_SEND_RETURN_CODE_AND_SETTING = 7
    
    
    class RES_CODE:
        GD_SUCCESS =                   0
        GD_FAIL =                      1
        GD_INCORRECT_PARAMETER =       2
        GD_INCORRECT_CMD_ID =          3
        GD_CMD_ID_NOT_EQUAL_IN_FLASH = 4
        GD_INCORRECT_DEVICE_ID =       5
    ##
    # @}
    
    
    
    # @brief Dynamic structure for metadata. Default should be invalid values
    class BRIDGE_METADATA:
        def __init__(self):
            self.i_MAX_CMD_ID = -1
            self.i_serial = -1
            self.s_descriptor = ""
            
        def __str__(self):
            return "Bridge>\n {0}\n Serial: {1}\n Max CMD ID: {2}\n"\
                    "<------------------------>"\
                .format(self.s_descriptor, self.i_serial, self.i_MAX_CMD_ID)
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief: Connect to the target device if possible
    def __init__(self):
        ##
        # @brief Global variables
        # @{
        
        ##
        # @brief Number of detected devices (-1 -> error -> so far none)
        self.i_num_of_devices = -1;
        
        # @}
        
        
        try:
            Uniprot_init()
            self.get_number_of_devices_from_device()
            
        except UniprotException_Device_not_found as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_Device_not_found("[Uniprot init] " +
                                                    str(e))
        
        except BridgeException_Device_not_found as e:
            Bridge.print_if_debug(str(e))
            raise UniprotException_Device_not_found("[Get num of dev] " +
                                                     str(e))
        
        except BridgeException_Device_RX_buffer_overflow as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_Device_RX_buffer_overflow("[Get num of dev] "
                                                         + str(e))
        
        except BridgeException_NACK_fail as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_NACK_fail("[Get num of dev] " + str(e))
        
        except BridgeException_Reset_fail as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_Reset_fail("[Get num of dev] " + str(e))
        
        # Try to get all metadata and save them to array
        self.s_metadata = []
        for i in range(self.i_num_of_devices +1):
            try:
                self.s_metadata.append(self.get_metadata_from_device(i))
            except BridgeException_Device_not_found as e:
                Bridge.print_if_debug(str(e))
                raise UniprotException_Device_not_found("[Get metadata] " +
                                                     str(e))
        
        
        
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    def close(self):
        try:
            Uniprot_close()
        except UniprotException_Device_not_found as e:
            # Even if this exception occurs, program can re-initialize device
            # if needed
            Bridge.print_if_debug(e)
            raise BridgeException_Device_not_found("[Uniprot close] " + str(e))
        
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief: Print message only if version is debug
    @classmethod
    def print_if_debug(cls, string):
        if Bridge.VERSION == "debug":
            print( string )
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#

    ##
    # @brief: Try to get number of devices connected to target
    # 
    # @return: Number of detected devices connected to target
    def get_number_of_devices_from_device(self):
        # Fill TX buffer
        i_tx_buffer = [0x00]*2
        # Device ID - ALWAYS MUST BE 0 !!!
        i_tx_buffer[0] = 0x00;  
        # Bridge command (request number)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_NUM_OF_DEV
        
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
                Bridge.print_if_debug(str(e))
                raise BridgeException_Device_not_found("[Uniprot TX data] "
                                                    + str(e))
                
            except UniprotException_NACK_fail as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_NACK_fail("[Uniprot TX data]" + str(e))
            
            except UniprotException_RX_buffer_overflow as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_Device_RX_buffer_overflow("[Uniprot TX data]"
                                                             + str(e))
                
            except UniprotException_Reset_success as e:
                Bridge.print_if_debug(str(e))
                # Send data once again
                i_retry_cnt = i_retry_cnt + 1
                if(i_retry_cnt > Bridge.MAX_RETRY_CNT):
                    Bridge.print_if_debug("[get_number_of_devices_from_device]"
                                          " Retry limit reached")
                    raise BridgeException_Reset_fail(" Reset retry count reach"
                                                 "maximum (TX data).")
            else:
                # If Uniprot_USB_tx_data end as expected -> no exception ->
                # -> break 
                break
            
            
            print_if_debug("Get number of devices status: " + status)
            
            
        # Reset counter
        i_retry_cnt = 0
        
        # When all OK, then RX data (expect from AVR)
        while(1):
            try:
                i_buffer_rx = Uniprot_USB_rx_data()
            except UniprotException_Device_not_found as e:
                print_if_debug("[get_number_of_devices_from_device]" + e)
                raise BridgeException_Device_not_found("[Uniprot RX data]"
                                                    + str(e))
            except UniprotException_Reset_success as e:
                Bridge.print_if_debug(\
                                    "[get_number_of_devices_from_device]" + str(e))
                # Send data once again
                i_retry_cnt = i_retry_cnt + 1
                if(i_retry_cnt > MAX_RETRY_CNT):
                    print_if_debug("[get_number_of_devices_from_device]"
                                          " Retry limit reached")
                    raise BridgeException_Reset_fail(" Reset retry count reach"
                                                 "maximum (RX data).")
            else:
                # If Uniprot_USB_rx_data end as expected -> no exception ->
                # -> break
                break
        
        # Test if send Device ID is correct
        if(i_buffer_rx[0] != 0):
            # This should not happen. It is not big problem, but it is not
            # standard behaviour
            print("[get_number_of_devices_from_device] Warning: Device ID"
                  " is not 0x00!")
        
        # Test if there is some problem on AVR side
        if(i_buffer_rx[1] == 0):
            # No problem, everything works
            
            self.i_num_of_devices = i_buffer_rx[2]
            # Send only number of devices (max. device index number)
            return i_buffer_rx[2]
    
        # Else exception - this never should happen
        raise BridgeException_Error("Error code from AVR is not 0, but it"
                                    " should be!")
        
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    def get_metadata_from_device(self, i_Device_ID):
        
        # Check if Device ID is valid
        if(i_Device_ID > self.i_num_of_devices):
            message = " Invalid Device ID. "
            if(i_num_of_devices < 0):
                message = message + "It looks that bridge was not" +\
                    " initialized. Please call function Uniprot_init() and"+\
                    " check all exceptions"
            else:
                # It look that bridge was initialized, but Device ID is invalid
                message = message + "Maximum Device ID is " +\
                                str(Bridge.i_num_of_devices) + " ."
            
            raise BridgeException_Error(message)
        
        
        
        # Fill TX buffer by zeros
        i_tx_buffer = [0x00]*2
        # Device ID
        i_tx_buffer[0] = i_Device_ID
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_METADATA
        
        
        
        # Configure TX packet
        Uniprot_config_TX_packet( 2 )
        
        # Configure RX packet
        Uniprot_config_RX_packet( Bridge.MAX_RX_BUFFER_BYTES )
        
        # Reset counter
        i_retry_cnt = 0
        
        while(1):
            try:
                # Try to send request
                status = Uniprot_USB_tx_data( i_tx_buffer )
                
            except UniprotException_Device_not_found as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_Device_not_found("[Uniprot TX data] "
                                                       + str(e))
                
            except UniprotException_NACK_fail as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_NACK_fail("[Uniprot TX data]" + str(e))
        
            except UniprotException_RX_buffer_overflow as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_Device_RX_buffer_overflow("[Uniprot"
                                                                " TX data]"
                                                             + str(e))
                
            except UniprotException_Reset_success as e:
                Bridge.print_if_debug(str(e))
                # Send data once again
                i_retry_cnt = i_retry_cnt + 1
                if(i_retry_cnt > MAX_RETRY_CNT):
                    Bridge.print_if_debug("[get_number_of_devices_from_device]"
                                          " Retry limit reached")
                    raise BridgeException_Reset_fail(" Reset retry count reach"
                                                     "maximum (TX data).")
            else:
                # Else TX data without exception -> break while
                break
            
            
        Bridge.print_if_debug("Get metadata status: " + status)
        
        # Reset counter
        i_retry_cnt = 0
        
        # RX data (metadata)
        while(1):
            try:
                i_buffer_rx = Uniprot_USB_rx_data()
                
            except UniprotException_Device_not_found as e:
                Bridge.print_if_debug("[get_number_of_devices_from_device]" + e)
                raise BridgeException_Device_not_found("[Uniprot RX data]"
                                                       + str(e))
            except UniprotException_Reset_success as e:
                Bridge.print_if_debug("[get_number_of_devices_from_device]" + e)
                # Send data once again
                i_retry_cnt = i_retry_cnt + 1
                if(i_retry_cnt > MAX_RETRY_CNT):
                    Bridge.print_if_debug("[get_number_of_devices_from_device]"
                                          " Retry limit reached")
                    raise BridgeException_Reset_fail(" Reset retry count"
                                            " reach maximum (RX data).")
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
            Bridge.print_if_debug("[bridge_get_metadata] Return code: " +
                                  str(i_buffer_rx[1]))
            # This never happen. Only one thing that may fail is wrong Device
            # ID, but this is checked before request is send. It can fail only
            # when whole protocol fail -> developer should fix this
            message = "Device returned code: " + str(i_buffer_rx[1]) +\
                 ". Please refer to source code what error code means."\
                 " However this should not happen. It is seems that there is"\
                 " some problem when transmitting or receiving data."
            raise BridgeException_Error(message)
        
        
        # Else all seems to be OK -> fill metadata structure
        rx_metadata = Bridge.BRIDGE_METADATA()
        
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
            rx_metadata.s_descriptor =   rx_metadata.s_descriptor +\
                                         str(unichr(i_buffer_rx[i_index]))
            
            # Increase index
            i_index = i_index+1
            
            
        # return metadata as object
        return rx_metadata
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    # @property - allow to handle with s_metadata as variable
    @property
    def device_metadata(self):
        return self.s_metadata
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    # Return maximum Device_ID, witch can be used as max index for metadata
    def get_max_Device_ID(self):
        return self.i_num_of_devices

#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#


#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#




