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

##
# @brief For logging events
import logging
import logging.config


from uniprot import *
from compiler.ast import Print
from cgi import log

## Load configure file for logging
logging.config.fileConfig('config/logging_global.conf', None, False)

##
# @brief Get logging variable
logger = logging.getLogger('Bridge HW <---> uniprot')



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
    MAX_RETRY_CNT = 30
    
    # In some cases should be defined maximum size of RX buffer
    MAX_RX_BUFFER_BYTES = 65530
    
    # Following constants must be same as in firmware (HW_bridge_uniprot)
    STATE_WAITING_FOR_REQUEST = 0
    STATE_REQUEST_GET_SETTING = 1
    STATE_REQUEST_SET_SETTING = 2
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
            return "Get setting\n\n DESCRIPTOR: {0}\n IN TYPE: {1}\n IN MIN:"\
                " {2}\n IN MAX: "\
                "{3}\n OUT TYPE: {4}\n OUT MIN: {5}\n OUT MAX: {6}\n "\
                "OUT VALUE: {7}\n<---------------------->\n"\
                .format(self.descriptor,\
                        Bridge.data_type_to_str(self.in_type),\
                        self.in_min,  self.in_max,\
                        Bridge.data_type_to_str(self.out_type),\
                         self.out_min, self.out_max,\
                        self.out_value)
    
    
    # @brief Dynamic structure for metadata. Default should be invalid values
    class BRIDGE_METADATA:
        def __init__(self):
            self.MAX_CMD_ID = -1
            self.serial = -1
            self.descriptor = ""
            
        def __str__(self):
            return "Bridge\n {0}\n Serial: {1}\n Max CMD ID: {2}\n"\
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
            logger.error("[__init__][Uniprot init]" + str(e))
            raise BridgeException_Device_not_found("[Uniprot init]" +
                                                    str(e))
        
        except BridgeException_Device_not_found as e:
            logger.error("[__init__][Get num of dev]" + str(e))
            raise UniprotException_Device_not_found("[Get num of dev]" +
                                                     str(e))
        
        except BridgeException_Device_RX_buffer_overflow as e:
            logger.critical("[__init__][Get num of dev]" + str(e))
            raise BridgeException_Device_RX_buffer_overflow("[Get num of dev]"
                                                         + str(e))
        
        except BridgeException_NACK_fail as e:
            logger.critical("[__init__][Get num of dev]" + str(e))
            raise BridgeException_NACK_fail("[Get num of dev]" + str(e))
        
        except BridgeException_Reset_fail as e:
            logger.critical("[__init__][Get num of dev]" + str(e))
            raise BridgeException_Reset_fail("[Get num of dev]" + str(e))
        
        
        # Try to get all metadata and save them to array
        self.s_metadata = []
        for i in range(self.i_num_of_devices +1):
            try:
                self.s_metadata.append(self.get_metadata_from_device(i))
            except BridgeException_Device_not_found as e:
                logger.error("[__init__][Get metadata]" + str(e))
                raise BridgeException_Device_not_found("[Get metadata]" +
                                                     str(e))
                
            except BridgeException_Device_RX_buffer_overflow as e:
                logger.critical("[__init__][Get metadata]" + str(e))
                raise BridgeException_Device_RX_buffer_overflow(
                            "[Get metadata]" + str(e))
                
            except BridgeException_NACK_fail as e:
                logger.critical("[__init__][Get metadata]" + str(e))
                raise BridgeException_NACK_fail("[Get metadata]" + str(e))
            
            except BridgeException_Reset_fail as e:
                logger.critical("[__init__][Get metadata]" + str(e))
                raise BridgeException_Reset_fail("[Get metadata]" + str(e))
        
        # Load actual configuration from device to RAM
        self.s_settings_in_RAM = []
        
        # Go thru all devices
        for i_DID in range(self.i_num_of_devices +1):
            # Thru all commands
            
            temp = []
            for i_CMD_ID in range(self.s_metadata[i_DID].MAX_CMD_ID +1):
                try:
                    temp.append(
                            self.get_setting_from_device(i_DID, i_CMD_ID))
                # And check all exceptions
                except BridgeException_Device_not_found as e:
                    logger.error("[__init__][Get setting]" + str(e))
                    raise BridgeException_Device_not_found("[Get setting]"
                                                           + str(e))
                
                except BridgeException_Device_RX_buffer_overflow as e:
                    logger.error("[__init__][Get setting]" + str(e))
                    raise BridgeException_Device_RX_buffer_overflow(
                                "[Get metadata]" + str(e))
                
                except BridgeException_NACK_fail as e:
                    logger.critical("[__init__][Get setting]" + str(e))
                    raise BridgeException_NACK_fail("[Get setting]" + str(e))
                
                except BridgeException_Reset_fail as e:
                    logger.critical("[__init__][Get setting]" + str(e))
                    raise BridgeException_Reset_fail("[Get setting]" + str(e))
                
                # If OK, then show info
                logger.info("[__init__][Get setting] "
                            "Get setting from DID: " + str(i_DID) +
                            " | CMD ID: " + str(i_CMD_ID) + " OK\n")
                
            self.s_settings_in_RAM.append(temp)
            
        
        for i_DID in range(self.i_num_of_devices +1):
            for i_CMD_ID in range(self.s_metadata[i_DID].MAX_CMD_ID +1):
                logger.debug("DID: " + str(i_DID) + " | CMD: "
                              + str(i_CMD_ID) + "\n" +
                             str(self.s_settings_in_RAM[i_DID][i_CMD_ID]))
        
        
        
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Close device (stop using USB interface)
    def close(self):
        try:
            Uniprot_close()
        except UniprotException_Device_not_found as e:
            # Even if this exception occurs, program can re-initialize device
            # if needed
            logger.error("[close][Uniprot close] " + str(e))
            raise BridgeException_Device_not_found("[Uniprot close] " + str(e))
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Convert result code number to string
    #
    # @param i_res_code: Code ID/number
    def res_code_to_str(self, i_res_code):
        if(i_res_code == Bridge.RES_CODE.GD_SUCCESS):
            return "Success"
        if(i_res_code == Bridge.RES_CODE.GD_FAIL):
            return "Fail"
        if(i_res_code == Bridge.RES_CODE.GD_CMD_ID_NOT_EQUAL_IN_FLASH):
            return "CMD ID is not equal with CMD ID found at flash on device"
        if(i_res_code == Bridge.RES_CODE.GD_INCORRECT_CMD_ID):
            return "Incorrect CMD ID"
        if(i_res_code == Bridge.RES_CODE.GD_INCORRECT_DEVICE_ID):
            return "Incorrect Device ID"
        if(i_res_code == Bridge.RES_CODE.GD_INCORRECT_PARAMETER):
            return "Incorrect input parameter"
        else:
            return "Unknown error. Please update software with device version"
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Convert data type number to string
    #
    # @param i_data_type: Code for data type
    @classmethod
    def data_type_to_str(cls, i_data_type):
        if(i_data_type == Bridge.DATA_TYPES.char_type):
            return "char"
        if(i_data_type == Bridge.DATA_TYPES.float_type):
            return "float"
        if(i_data_type == Bridge.DATA_TYPES.int16_type):
            return "int16"
        if(i_data_type == Bridge.DATA_TYPES.int32_type):
            return "int32"
        if(i_data_type == Bridge.DATA_TYPES.int8_type):
            return "int8"
        if(i_data_type == Bridge.DATA_TYPES.int_type):
            return "int (16b)"
        if(i_data_type == Bridge.DATA_TYPES.uint16_type):
            return "uint16"
        if(i_data_type == Bridge.DATA_TYPES.uint32_type):
            return "uint32"
        if(i_data_type == Bridge.DATA_TYPES.uint8_type):
            return "uint8"
        if(i_data_type == Bridge.DATA_TYPES.uint_type):
            return "uint (16b)"
        if(i_data_type == Bridge.DATA_TYPES.void_type):
            return "void"
        else:
            return "Unknown data type. Please update software with device version"
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Send request and get response
    #
    # TX packet and RX packet must be configured before call this function
    #
    # @param i_tx_buffer: Data to send
    # @return: received data 
    def send_request_get_data(self, i_tx_buffer):
        # Reset retry count
        i_retry_cnt = 0
        
        # Inform if request should be transmitted again
        send_request_again = 0
        
        # Main loop - TX data + RX data
        while(1):
            # Reset value -> request will be send anyway (next while)
            send_request_again = 0
            # Secondary loop - try TX data
            while(1):
                if(i_retry_cnt > 0):
                    logger.warn("[send_request_get_data][Uniprot TX data]"
                                " Retry count: " + str(i_retry_cnt) + "\n")
                try:
                    # Try to send request
                    status = Uniprot_USB_tx_data( i_tx_buffer )
                
                except UniprotException_Device_not_found as e:
                    logger.error("[send_request_get_data]"
                                 "[Uniprot TX data]"
                                 + str(e))
                    raise BridgeException_Device_not_found("[Uniprot TX data]"
                                                           + str(e))
                
                except UniprotException_NACK_fail as e:
                    logger.critical("[send_request_get_data]"
                                    "[Uniprot TX data]"
                                    + str(e))
                    raise BridgeException_NACK_fail("[Uniprot TX data]"
                                                     + str(e))
                
                except UniprotException_RX_buffer_overflow as e:
                    logger.critical("[send_request_get_data]"
                                    "[Uniprot TX data]"
                                    + str(e))
                    raise BridgeException_Device_RX_buffer_overflow("[Uniprot"
                                                                    " TX data]"
                                                                    + str(e))
                
                except UniprotException_Reset_success as e:
                    logger.warn("[send_request_get_data]"
                                "[Uniprot TX data]"
                                + str(e))
                    # Send data once again
                    i_retry_cnt = i_retry_cnt + 1
                    if(i_retry_cnt > Bridge.MAX_RETRY_CNT):
                        logger.critical("[send_request_get_data]"
                                        " Reset retry count reach"
                                        "maximum (TX data).\n")
                        raise BridgeException_Reset_fail(" Reset retry count"
                                                         " reach maximum"
                                                         " (TX data).\n")
                else:
                    # Else TX data without exception -> break while
                    break
            
            
            logger.debug("[send_request_get_data]"
            " Request status: " + status + "\n")
            
            # Secondary loop - try RX data
            
            # RX data (one setting)
            while(1):
                if(i_retry_cnt > 0):
                    logger.warn("[send_request_get_data][Uniprot RX data]"
                                " Retry count: " + str(i_retry_cnt) + "\n")
                try:
                    i_rx_buffer = Uniprot_USB_rx_data()
                except UniprotException_Device_not_found as e:
                    logger.error("[send_request_get_data][Uniprot RX data]"
                                 + str(e))
                    raise BridgeException_Device_not_found("[Uniprot RX data]"
                                                           + str(e))
                except UniprotException_Reset_success as e:
                    logger.warn("[send_request_get_data][Uniprot RX data]"
                                 + str(e))
                    # Send data once again
                    i_retry_cnt = i_retry_cnt + 1
                    if(i_retry_cnt > Bridge.MAX_RETRY_CNT):
                        logger.critical("[send_request_get_data]"
                                        "[Uniprot RX data]"
                                        " Reset retry count"
                                        " reach maximum (RX data).\n")
                        raise BridgeException_Reset_fail(" Reset retry count"
                                                         " reach maximum"
                                                         " (RX data).\n")
                    else:
                        # Must send request again (reset was done, so
                        # everything is set to default -> request was removed.
                        # So, set send_request_again to 1 and break this while
                        # to get to TX while
                        send_request_again = 1
                        break 
                else:
                    # Else no exception -> break while
                    break
            # Test if all OK (send_request_again = 0) or if request should be
            # send once again due to reset
            if(send_request_again == 0):
                # If all OK -> break even main while cycle 
                break
        
        # If all OK -> return RX data
        return i_rx_buffer
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
        
        
        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeException_Device_not_found as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeException_Device_not_found(message)
        
        except BridgeException_NACK_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeException_NACK_fail(message)
        
        except BridgeException_Device_RX_buffer_overflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeException_Device_RX_buffer_overflow(message)
        
        except BridgeException_Reset_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeException_Reset_fail(message)
        
       
        # Test if send Device ID is correct
        if(i_rx_buffer[0] != 0):
            # This should not happen. It is not big problem, but it is not
            # standard behaviour
            logger.warn("[get_number_of_devices_from_device]"
                           "[Uniprot RX data] Device ID is not 0x00!")
        
        # Test if there is some problem on AVR side
        if(i_rx_buffer[1] == 0):
            # No problem, everything works
            
            self.i_num_of_devices = i_rx_buffer[2]
            # Send only number of devices (max. device index number)
            return i_rx_buffer[2]
        
        
        logger.error("[get_number_of_devices_from_device]"
                     " Error code from AVR is not 0, but it should be!"
                     " Error: "+ self.res_code_to_str(i_rx_buffer[1]) + "\n")
        
        # Else exception - this never should happen
        raise BridgeException_Error(" Error code from AVR is not 0, but it"
                                    " should be!\n")
        
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
                    " check all exceptions.\n"
            else:
                # It look that bridge was initialized, but Device ID is invalid
                message = message + "Maximum Device ID is " +\
                                str(self.i_num_of_devices) + " .\n"
            
            logger.warn("[get_metadata_from_device]" + message)
            
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
        
        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeException_Device_not_found as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeException_Device_not_found(message)
        
        except BridgeException_NACK_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeException_NACK_fail(message)
        
        except BridgeException_Device_RX_buffer_overflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeException_Device_RX_buffer_overflow(message)
        
        except BridgeException_Reset_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeException_Reset_fail(message)
        
        
        
        
        
        # Test if received Device ID is same
        if(i_rx_buffer[0] != i_Device_ID):
            # This should not happen.
            message = " Got different Device ID (" + str(i_rx_buffer[0]) +\
            "), but expected " + str(i_Device_ID) + " . This is failure of"\
            "communication protocol."
            logger.warn("[get_metadata_from_device]" + message)
            raise BridgeException_Error(message)
        
        # Test return code - never should happen, but...
        if(i_rx_buffer[1] != 0):
            # This never happen. Only one thing that may fail is wrong Device
            # ID, but this is checked before request is send. It can fail only
            # when whole protocol fail -> developer should fix this
            message = "Device returned code: "\
                 + self.res_code_to_str(i_rx_buffer[1]) +\
                 " This should not happen. It is seems that there is"\
                 " some problem when transmitting or receiving data."
            logger.critical("[get_metadata_from_device]"
                            "[Uniprot RX data]"
                             + message)
            raise BridgeException_Error(message)
        
        
        # Else all seems to be OK -> fill metadata structure
        rx_metadata = Bridge.BRIDGE_METADATA()
        
        # Metadata begin at index 2 (3rd byte)
        i_index = 2
        
        # Load MAX CMD ID
        rx_metadata.MAX_CMD_ID = (i_rx_buffer[i_index])<<8
        i_index = i_index+1
        rx_metadata.MAX_CMD_ID = rx_metadata.MAX_CMD_ID + i_rx_buffer[i_index]
        i_index = i_index+1
        
        # Load serial number
        rx_metadata.serial = i_rx_buffer[i_index]
        i_index = i_index+1
        
        # Clear descriptor
        rx_metadata.descriptor = ""
        
        # Load descriptor
        while(i_rx_buffer[i_index] != 0x00):
            # Add character to descriptor
            rx_metadata.descriptor =   rx_metadata.descriptor +\
                                         str(unichr(i_rx_buffer[i_index]))
            
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
                                str(self.i_num_of_devices) + " .\n"
            
            logger.warn("[get_setting_from_device]" + message)
            
            raise BridgeException_Error(message)
        
        if(i_Device_ID < 0):
            logger.warn("[get_setting_from_device]"
                        "Invalid i_Device_ID. Can not be lower than 0")
            raise BridgeException_Error("Invalid i_Device_ID. Can not be"
                                        " lower than 0")
        
        # Check i_CMD_ID
        if((i_CMD_ID > self.device_metadata[i_Device_ID].MAX_CMD_ID) or\
           (i_CMD_ID < 0)):
            message = " Invalid CMD ID (input parameter: " +\
                        str(i_CMD_ID) + ").\n Minimum CMD ID is 0. Maximum CMD"\
                        " ID for device " + str(i_Device_ID) + " is " +\
                        str(self.device_metadata[i_Device_ID].MAX_CMD_ID) +\
                        "\n"
                        
            logger.warn("[get_setting_from_device]" + message)
            raise BridgeException_Error(message)
        if(i_CMD_ID > 0xFFFF):
            logger.warn("[get_setting_from_device]"
                        " i_CMD_ID is longer than 2B. Protocol send just"
                        " 2 LSB Bytes.\n")
            i_CMD_ID = i_CMD_ID & 0xFFFF
        
        
        # Fill TX buffer by zeros
        i_tx_buffer = [0x00]*4
        # Device ID
        i_tx_buffer[0] = i_Device_ID
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_SETTING
        # CMD ID - must be split into two Bytes
        i_tx_buffer[2] = (i_CMD_ID >> 8)
        i_tx_buffer[3] = (i_CMD_ID)      & 0xFF
        
        
        
        # Configure TX packet
        Uniprot_config_TX_packet( 4 )
        
        # Configure RX packet
        Uniprot_config_RX_packet( Bridge.MAX_RX_BUFFER_BYTES )
        
        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeException_Device_not_found as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeException_Device_not_found(message)
        
        except BridgeException_NACK_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeException_NACK_fail(message)
        
        except BridgeException_Device_RX_buffer_overflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeException_Device_RX_buffer_overflow(message)
        
        except BridgeException_Reset_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeException_Reset_fail(message)
        
        
        # Test if received DID is same
        if(i_rx_buffer[0] != i_Device_ID):
            # This should not happen.
            message = " Got different Device ID (" + str(i_rx_buffer[0]) +\
               "), but expected " + str(i_Device_ID) + " . This is failure of"\
               "communication protocol.\n"
            logger.error("[get_setting_from_device]"
                         + message)
            raise BridgeException_Error(message)
            
        # Check return code - should be 0, else there is bug in protocol
        if(i_rx_buffer[1] != 0):
            # This never happen. Only one thing that may fail is wrong Device
            # ID, but this is checked before request is send. It can fail only
            # when whole protocol fail -> developer should fix this
            message = " Device returned code: "\
                    + self.res_code_to_str(i_rx_buffer[1]) +\
                    ". Please refer to source code what error code means."\
                    " However this should not happen. It is seems that there"\
                    " is some problem when transmitting or receiving data."
            logger.critical("[get_setting_from_device]" + message)
            raise BridgeException_Error(message)
            
        # Check CMD ID
        if(((i_rx_buffer[2]<<8) + i_rx_buffer[3]) != i_CMD_ID):
            message = " Device returned different CMD ID (" +\
                    str((i_rx_buffer[2]<<8) + i_rx_buffer[3]) +\
                    "), but expected " + \
                    str(i_CMD_ID) + ". This means failure on protocol layer."
            logger.critical("[get_setting_from_device]" + message)
            raise BridgeException_Error(message)
            
        # Else all seems to be OK -> fill structure
        rx_config = Bridge.SETTING_STRUCT()
        
        # Index for rx_buffer - begin at 4
        i_index_rx_buffer = 4
        
        # Load data to struct (load byte by byte)
        
        # IN TYPE
        rx_config.in_type = i_rx_buffer[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # IN MIN
        rx_config.in_min =  (i_rx_buffer[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_min =  rx_config.in_min +\
                            (i_rx_buffer[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_min =  rx_config.in_min +\
                            (i_rx_buffer[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_min =  rx_config.in_min +\
                            (i_rx_buffer[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # IN MAX
        rx_config.in_max =  (i_rx_buffer[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_max =  rx_config.in_max +\
                            (i_rx_buffer[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_max =  rx_config.in_max +\
                            (i_rx_buffer[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.in_max =  rx_config.in_max +\
                            (i_rx_buffer[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT TYPE
        rx_config.out_type = i_rx_buffer[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT MIN
        rx_config.out_min = (i_rx_buffer[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_min = rx_config.out_min +\
                            (i_rx_buffer[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_min = rx_config.out_min +\
                            (i_rx_buffer[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_min = rx_config.out_min +\
                            (i_rx_buffer[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT MAX
        rx_config.out_max = (i_rx_buffer[i_index_rx_buffer]<<24)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_max = rx_config.out_max +\
                            (i_rx_buffer[i_index_rx_buffer]<<16)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_max = rx_config.out_max +\
                            (i_rx_buffer[i_index_rx_buffer]<<8)
        i_index_rx_buffer = i_index_rx_buffer +1
        rx_config.out_max = rx_config.out_max +\
                            i_rx_buffer[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer +1
        
        
        # OUT VALUE
        rx_config.out_value =   (i_rx_buffer[i_index_rx_buffer]<<24)
        i_index_rx_buffer   =   i_index_rx_buffer +1
        rx_config.out_value =   rx_config.out_value +\
                                (i_rx_buffer[i_index_rx_buffer]<<16)
        i_index_rx_buffer   =   i_index_rx_buffer +1
        rx_config.out_value =   rx_config.out_value +\
                                (i_rx_buffer[i_index_rx_buffer]<<8)
        i_index_rx_buffer   =   i_index_rx_buffer +1
        rx_config.out_value =   rx_config.out_value +\
                                i_rx_buffer[i_index_rx_buffer]
        i_index_rx_buffer   =   i_index_rx_buffer +1
        
        
        # And get descriptor - do not know length
        while(i_rx_buffer[i_index_rx_buffer] != 0x00):
            # Add character to string
            rx_config.descriptor = rx_config.descriptor + \
                            str(unichr(i_rx_buffer[i_index_rx_buffer]))
            i_index_rx_buffer = i_index_rx_buffer +1
        
        
        
        return rx_config

#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    # Try to set setting and if success try to read and update actual value
    # using get setting
    def set_setting_to_device(self, i_Device_ID, i_CMD_ID, i_value):
        # Check Device ID
        if(i_Device_ID > self.i_num_of_devices):
            message = " Invalid Device ID. "
            if(self.i_num_of_devices < 0):
                message = message + "It looks that bridge was not"\
                    " initialized. Please call function Uniprot_init() and"+\
                    " check all exceptions"
            else:
                # It looks that bridge was initialized, but device ID is invalid
                message = message + "Maximum Device ID is " +\
                                str(self.i_num_of_devices) + " .\n"
            logger.warn("[set_setting_to_device]" + message)
            
            raise BridgeException_Error(message)
        
        if(i_Device_ID < 0):
            message = "Invalid i_Device_ID. Can not be lower than 0"
            logger.warn("[set_setting_from_device]"
                        + message)
            raise BridgeException_Error(message)
        
        
        
        # Now check CMD ID
        if((i_CMD_ID > self.s_metadata[i_Device_ID].MAX_CMD_ID) or
           (i_CMD_ID < 0)):
            message = "Invalid CMD ID. Can not be lower than 0 and higher"\
                      " then " + str(self.s_metadata[i_Device_ID].MAX_CMD_ID)\
                      + " for device " + str(i_Device_ID) + " .\n"
            logger.warn("[set_setting_from_device]"
                        + message)
            raise BridgeException_Error(message)
        if(i_CMD_ID > 0xFFFF):
            logger.warn("[set_setting_to_device]"
                        " i_CMD_ID is longer than 2B. Protocol send just"
                        " 2 LSB Bytes.\n")
            i_CMD_ID = i_CMD_ID & 0xFFFF
        
        
        # Grab i_value and check if is maximum 4B long
        if((i_value & 0xFFFFFFFF) < i_value):
            logger.warn("[set_setting_to_device]"
                        " i_value is longer than 4B."
                        " Transmit only LSB 4Bytes.\n")
            # Use only 4 LSB Bytes
            i_value = i_value & 0xFFFFFFFF
        
        
        # Fill TX buffer by zeros
        i_tx_buffer = [0x00]*8
        # Device ID
        i_tx_buffer[0] = i_Device_ID
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_SET_SETTING
        # CMD ID - must be split into two Bytes
        i_tx_buffer[2] = (i_CMD_ID >> 8)
        i_tx_buffer[3] = (i_CMD_ID)      & 0xFF
        # i_value - 4B - split
        i_tx_buffer[4] = (i_value >> 24)
        i_tx_buffer[5] = (i_value >> 16) & 0xFF
        i_tx_buffer[6] = (i_value >>  8) & 0xFF
        i_tx_buffer[7] =  i_value        & 0xFF
        
        
        # Configure TX packet
        Uniprot_config_TX_packet( 8 )
        
        # Configure RX packet
        Uniprot_config_RX_packet( Bridge.MAX_RX_BUFFER_BYTES )
        
        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeException_Device_not_found as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_Device_not_found(message)
        
        except BridgeException_NACK_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_NACK_fail(message)
        
        except BridgeException_Device_RX_buffer_overflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_Device_RX_buffer_overflow(message)
        
        except BridgeException_Reset_fail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_Reset_fail(message)
        
        
        # Test if received DID is same
        if(i_rx_buffer[0] != i_Device_ID):
            # This should not happen.
            message = " Got different Device ID (" + str(i_rx_buffer[0]) +\
               "), but expected " + str(i_Device_ID) + " . This is failure of"\
               "communication protocol.\n"
            logger.error("[set_setting_to_device]"
                         + message)
            raise BridgeException_Error(message)
            
        # Check return code - should be 0, however it cant't
        if(i_rx_buffer[1] != 0):
            message = " Device returned code: "\
                     + self.res_code_to_str(i_rx_buffer[1]) + "\n"
            logger.warning("[set_setting_to_device]" + message)
            raise BridgeException_Error(message)
        
        
        # Setting was set, but program should update value -> call 
        # get_setting_from_device and update data in RAM
        try:
            self.s_settings_in_RAM[i_Device_ID][i_CMD_ID] =\
                        self.get_setting_from_device(i_Device_ID, i_CMD_ID)
        except BridgeException_Device_not_found as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_Device_not_found(message)
        
        except BridgeException_NACK_fail as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_NACK_fail(message)
        
        except BridgeException_Device_RX_buffer_overflow as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_Device_RX_buffer_overflow(message)
        
        except BridgeException_Reset_fail as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeException_Reset_fail(message)
        
        
        # If no exception occurred -> return result code as text
        return self.res_code_to_str(i_rx_buffer[1])



#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # Return metadata of all devices as variable
    # @property - allow to handle with s_metadata as variable
    @property
    def device_metadata(self):
        return self.s_metadata
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # Return maximum Device_ID, witch can be used as max index for metadata
    def get_max_Device_ID(self):
        return self.i_num_of_devices
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # Return complex device settings as one object
    @property
    def get_all_settings(self):
        return self.s_settings_in_RAM
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#






