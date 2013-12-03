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
#  # Get downloaded metadata. User can select device thru index. Maximum index
#  # is max_DID. 
#  print(bridge.get_metadata[max_DID])
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
    
    # This definitions must be same on AVR too!
    class DATA_TYPES:
        void_type =                     0
        
        char_type =                     1
        
        int_type =                      2
        int8_type =                     3
        int16_type =                    4
        int32_type =                    5
        
        uint_type =                     6
        uint8_type =                    7
        uint16_type =                   8
        uint32_type =                   9
        
        float_type =                    10
    
    
    ##
    # @}
    
    
    # Structure for get/set setting functions
    class SETTING_STRUCT:
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
            return "Get settings>\n IN TYPE: {0}\n IN MIN: {1}\n IN MAX: "\
                "{2}\n OUT TYPE: {3}\n OUT MIN: {4}\n OUT MAX: {5}\n "\
                "OUT VALUE: {6}\n DESCRIPTOR: {7}\n<---------------------->"\
                .format(self.in_type,  self.in_min,  self.in_max,\
                        self.out_type, self.out_min, self.out_max,\
                        self.out_value, self.descriptor)
    
    
    # @brief Dynamic structure for metadata. Default should be invalid values
    class BRIDGE_METADATA:
        def __init__(self):
            self.MAX_CMD_ID = -1
            self.serial = -1
            self.descriptor = ""
            
        def __str__(self):
            return "Bridge>\n {0}\n Serial: {1}\n Max CMD ID: {2}\n"\
                    "<------------------------>"\
                .format(self.descriptor, self.serial, self.MAX_CMD_ID)
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
            raise BridgeException_Device_not_found("[Uniprot init]" +
                                                    str(e))
        
        except BridgeException_Device_not_found as e:
            Bridge.print_if_debug(str(e))
            raise UniprotException_Device_not_found("[Get num of dev]" +
                                                     str(e))
        
        except BridgeException_Device_RX_buffer_overflow as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_Device_RX_buffer_overflow("[Get num of dev]"
                                                         + str(e))
        
        except BridgeException_NACK_fail as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_NACK_fail("[Get num of dev]" + str(e))
        
        except BridgeException_Reset_fail as e:
            Bridge.print_if_debug(str(e))
            raise BridgeException_Reset_fail("[Get num of dev]" + str(e))
        
        # Try to get all metadata and save them to array
        self.s_metadata = []
        for i in range(self.i_num_of_devices +1):
            try:
                self.s_metadata.append(self.get_metadata_from_device(i))
            except BridgeException_Device_not_found as e:
                Bridge.print_if_debug(str(e))
                raise UniprotException_Device_not_found("[Get metadata]" +
                                                     str(e))
                
            except BridgeException_Device_RX_buffer_overflow as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_Device_RX_buffer_overflow(
                            "[Get metadata]" + str(e))
                
            except BridgeException_NACK_fail as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_NACK_fail("[Get metadata]" + str(e))
            
            except BridgeException_Reset_fail as e:
                Bridge.print_if_debug(str(e))
                raise BridgeException_Reset_fail("[Get metadata]" + str(e))
        
        
        
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
            if(self.i_num_of_devices < 0):
                message = message + "It looks that bridge was not" +\
                    " initialized. Please call function Uniprot_init() and"+\
                    " check all exceptions"
            else:
                # It look that bridge was initialized, but Device ID is invalid
                message = message + "Maximum Device ID is " +\
                                str(self.i_num_of_devices) + " ."
            
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
        
        # Test if received Device ID is same
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
        rx_metadata.MAX_CMD_ID = (i_buffer_rx[i_index])<<8
        i_index = i_index+1
        rx_metadata.MAX_CMD_ID = rx_metadata.MAX_CMD_ID + i_buffer_rx[i_index]
        i_index = i_index+1
        
        # Load serial number
        rx_metadata.serial = i_buffer_rx[i_index]
        i_index = i_index+1
        
        # Clear descriptor
        rx_metadata.descriptor = ""
        
        # Load descriptor
        while(i_buffer_rx[i_index] != 0x00):
            # Add character to descriptor
            rx_metadata.descriptor =   rx_metadata.descriptor +\
                                         str(unichr(i_buffer_rx[i_index]))
            
            # Increase index
            i_index = i_index+1
            
            
        # return metadata as object
        return rx_metadata
    
    
    
    
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#    
    # Try to get setting (one) from device
    def get_setting_from_device(self, i_Device_ID, i_CMD_ID):
        
        # Check if Device ID is valid
        if(i_Device_ID > self.i_num_of_devices):
            message = " Invalid Device ID. "
            if(self.i_num_of_devices < 0):
                message = message + "It looks that bridge was not"\
                    " initialized. Please call function Uniprot_init() and"+\
                    " check all exceptions"
            else:
                # It look that bridge was initialized, but Device ID is invalid
                message = message + "Maximum Device ID is " +\
                                str(self.i_num_of_devices) + " ."
            
            raise BridgeException_Error(message)
        
        if(i_Device_ID < 0):
            raise BridgeException_Error("Invalid i_Device_ID. Can not be"
                                        " lower than 0")
        
        # Check i_CMD_ID
        if((i_CMD_ID > self.device_metadata[i_Device_ID].MAX_CMD_ID) or\
           (i_CMD_ID < 0)):
            raise BridgeException_Error(" Invalid CMD ID (input parameter: " +\
                        str(i_CMD_ID) + ").\n Minimum CMD ID is 0. Maximum CMD"
                        " ID for device " + str(i_Device_ID) + " is " +\
                        str(self.device_metadata[i_Device_ID].MAX_CMD_ID))
        
        # Fill TX buffer by zeros
        i_tx_buffer = [0x00]*4
        # Device ID
        i_tx_buffer[0] = i_Device_ID
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_SETTINGS
        # CMD ID - must be split into two Bytes
        i_tx_buffer[2] = (i_CMD_ID >> 8) & 0xFF
        i_tx_buffer[3] = (i_CMD_ID)      & 0xFF
        
        
        
        # Configure TX packet
        Uniprot_config_TX_packet( 4 )
        
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
                    Bridge.print_if_debug("[get_setting_from_device]"
                                          " Retry limit reached")
                    raise BridgeException_Reset_fail(" Reset retry count reach"
                                                     "maximum (TX data).")
            else:
                # Else TX data without exception -> break while
                break
            
            
        Bridge.print_if_debug("Get setting: " + status)
        
        # RX data (one setting)
        while(1):
            try:
                i_buffer_rx = Uniprot_USB_rx_data()
                
            except UniprotException_Device_not_found as e:
                Bridge.print_if_debug("[get_setting_from_device]" + e)
                raise BridgeException_Device_not_found("[Uniprot RX data]"
                                                       + str(e))
            except UniprotException_Reset_success as e:
                Bridge.print_if_debug("[get_setting_from_device]" + e)
                # Send data once again
                i_retry_cnt = i_retry_cnt + 1
                if(i_retry_cnt > MAX_RETRY_CNT):
                    Bridge.print_if_debug("[get_setting_from_device]"
                                          " Retry limit reached")
                    raise BridgeException_Reset_fail(" Reset retry count"
                                            " reach maximum (RX data).")
            else:
                # Else no exception -> break while
                break
            
        Bridge.print_if_debug("Get setting: RX data OK")
        
        # Test if received DID is same
        if(i_buffer_rx[0] != i_Device_ID):
            # This should not happen.
            message = " Got different Device ID (" + str(i_buffer_rx[0]) +\
               "), but expected " + str(i_Device_ID) + " . This is failure of"\
               "communication protocol."
            raise BridgeException_Error(message)
            
        # Check return code - should be 0, else there is bug in protocol
        if(i_buffer_rx[1] != 0):
            Bridge.print_if_debug("[get_setting_from_device] Return code: " +
                                  str(i_buffer_rx[1]))
            # This never happen. Only one thing that may fail is wrong Device
            # ID, but this is checked before request is send. It can fail only
            # when whole protocol fail -> developer should fix this
            message = "Device returned code: " + str(i_buffer_rx[1]) +\
                    ". Please refer to source code what error code means."\
                    " However this should not happen. It is seems that there"\
                    " is some problem when transmitting or receiving data."
            raise BridgeException_Error(message)
            
        # Check CMD ID
        if(((i_buffer_rx[2]<<8) + i_buffer_rx[3]) != i_CMD_ID):
            Bridge.print_if_debug("[get_setting_from_device]"
                                      " TX CMD ID: " + str(i_CMD_ID) + 
                                      "RX CMD ID: " + str(i_buffer_rx[2]))
            message = "Device returned different CMD ID (" +\
                    str((i_buffer_rx[2]<<8) + i_buffer_rx[3]) +\
                    "), but expected " + \
                    str(i_CMD_ID) + ". This means failure on protocol layer."
            raise BridgeException_Error(message)
            
        # Else all seems to be OK -> fill structure
        rx_config = Bridge.SETTING_STRUCT()
        
        # Index for rx_buffer - begin at 4
        i_index_rx_buffer = 4
        
        # Load data to struct (load byte by byte)
        
        # IN TYPE
        rx_config.in_type = i_buffer_rx[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # IN MIN
        rx_config.in_min =  (i_buffer_rx[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_min =  rx_config.in_min +\
                            (i_buffer_rx[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_min =  rx_config.in_min +\
                            (i_buffer_rx[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_min =  rx_config.in_min +\
                            (i_buffer_rx[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # IN MAX
        rx_config.in_max =  (i_buffer_rx[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_max =  rx_config.in_max +\
                            (i_buffer_rx[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_max =  rx_config.in_max +\
                            (i_buffer_rx[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_max =  rx_config.in_max +\
                            (i_buffer_rx[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT TYPE
        rx_config.out_type = i_buffer_rx[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT MIN
        rx_config.out_min = (i_buffer_rx[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_min = rx_config.out_min +\
                            (i_buffer_rx[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_min = rx_config.out_min +\
                            (i_buffer_rx[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_min = rx_config.out_min +\
                            (i_buffer_rx[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT MAX
        rx_config.out_max = (i_buffer_rx[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_max = rx_config.out_max +\
                            (i_buffer_rx[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_max = rx_config.out_max +\
                            (i_buffer_rx[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_max = rx_config.out_max +\
                            i_buffer_rx[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT VALUE
        rx_config.out_value =   (i_buffer_rx[i_index_rx_buffer]<<24)
        i_index_rx_buffer   =   i_index_rx_buffer +1
        rx_config.out_value =   rx_config.out_value +\
                                (i_buffer_rx[i_index_rx_buffer]<<16)
        i_index_rx_buffer   =   i_index_rx_buffer +1
        rx_config.out_value =   rx_config.out_value +\
                                (i_buffer_rx[i_index_rx_buffer]<<8)
        i_index_rx_buffer   =   i_index_rx_buffer +1
        rx_config.out_value =   rx_config.out_value +\
                                i_buffer_rx[i_index_rx_buffer]
        i_index_rx_buffer   =   i_index_rx_buffer +1
        
        
        # And get descriptor - do not know length
        while(i_buffer_rx[i_index_rx_buffer] != 0x00):
            # Add character to string
            rx_config.descriptor = rx_config.descriptor + \
                            str(unichr(i_buffer_rx[i_index_rx_buffer]))
            i_index_rx_buffer = i_index_rx_buffer +1
        
        
        
        return rx_config
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




