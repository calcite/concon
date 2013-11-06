#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
#
# @brief Universal protocol designed for 8 bit embedded systems
#
# 
#
# @author Martin Stejskal
#


from crc16_xmodem import *
from driver_usb import *


##
# @brief "Constants"
# @{
# options: debug, release
const_uniprot_VERSION = "debug"

const_USB_VID = 0x03EB

const_USB_PID = 0x204F

const_UNI_CHAR_HEADER = ord('H')

const_UNI_CHAR_DATA = ord('D')

const_UNI_CHAR_TAIL = ord('T')

const_UNI_CHAR_ACK = ord('A')

const_UNI_CHAR_NACK = ord('N')

const_UNI_CHAR_RESET = ord('R')

const_UNI_CHAR_BUFFER_OVERFLOW = ord('O')


const_UNI_RES_CODE_CRC_ERROR = "CRC ERROR"

const_UNI_RES_CODE_ACK = "ACK"

const_UNI_RES_CODE_NACK = "NACK"

const_UNI_RES_CODE_RX_BUFFER_OVERFLOW = "RX BUFFER OVERFLOW"

const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW = "DEVICE BUFFER OVERFLOW"

const_UNI_RES_CODE_RESET = "RESET"

const_UNI_RES_CODE_UNKNOWN_COMMAND = "FATAL ERROR! UNKNOWN COMMAND"

const_UNI_RES_CODE_SUCCESS = "Yes, all OK!"

const_UNI_RES_CODE_DEVICE_NOT_FOUND = "Device not found. Please make sure that device is connected"
##
# @}


##
# @{ Structures/Classes

##
# @brief Structure for packet configuration
class UNI_PACKET_CONFIG:
    i_rx_num_of_data_Bytes = 0
    i_rx_config_done = False
    
    i_tx_num_of_data_Bytes = 0
    i_tx_config_done = False

##
# @brief Structure for status (error codes and flags)
class UNI_STATUS:
    UNI_SR_ERROR_FLAG_TX_NOT_CONFIGURED = False
    UNI_SR_ERROR_FLAG_RX_NOT_CONFIGURED = False
    UNI_SR_WAITING_FOR_ACK              = False
    UNI_SR_SENDING_ACK                  = False
    UNI_SR_ERROR_FLAG_HEADER_RX         = False
    UNI_SR_ERROR_FLAG_CRC_RX            = False
    UNI_SR_ERROR_FLAG_TAIL_RX           = False
    UNI_SR_ERROR_FLAG_GENERAL_RX        = False
    UNI_SR_ERROR_FLAG_GENERAL_TX        = False
    UNI_SR_ERROR_FLAG_OVERFLOW_RX       = False
    UNI_SR_FLAG_RX_DONE                 = False
    UNI_SR_FLAG_TX_DONE                 = False
    
# @}


##
# @brief Global variables
# @{

# Configuration for packet
s_packet_config = UNI_PACKET_CONFIG()

# Status "register"
s_status        = UNI_STATUS()

# Buffer for receiving
i_buffer_rx = None

# Define device - default 404 - device not found yet
device = 404
# @}




##
# @brief Print message only if version is debug
def print_if_debug_uniprot( string ):
    global const_uniprot_VERSION
    if const_uniprot_VERSION == "debug":
        print( string )





##
# @brief Connect to the target device if possible
def Uniprot_init():
    global device
    global const_USB_VID
    global const_USB_PID
    
    device = usb_open_device(const_USB_VID, const_USB_PID)
    
    if(device == 404):
        return 404
    else:
        return 0


##
# @brief Disconnect from the target device if possible
def Uniprot_close():
    global const_USB_VID
    global const_USB_PID
    
    status = usb_close_device(const_USB_VID, const_USB_PID)
    return status


##
# @brief Configure TX packet - define data frames
#
# Because in protocol algorithm need to know how many bytes should send,
# programmer must define how many Bytes should be send
#
# @param i_tx_num_of_data_Bytes Number of data Bytes
def Uniprot_config_TX_packet( i_tx_num_of_data_Bytes):
    global s_packet_config
    
    s_packet_config.i_tx_num_of_data_Bytes = i_tx_num_of_data_Bytes
    
    s_packet_config.i_tx_config_done = True
    
    # Test if there is any problem with TX device
    if( s_status.UNI_SR_ERROR_FLAG_GENERAL_TX == False ):
        # If there is not any problem -> set TX_done flag
        s_status.UNI_SR_FLAG_TX_DONE = True

##
# @brief Configure RX packet - define data frames
#
# Because in protocol algorithm need to know how many bytes should receive,
# programmer must define how many Bytes should be received
#
# @param i_rx_num_of_data_Bytes Number of data Bytes
def Uniprot_config_RX_packet( i_rx_num_of_data_Bytes):
    global s_packet_config
    
    s_packet_config.i_rx_num_of_data_Bytes = i_rx_num_of_data_Bytes
    
    s_packet_config.i_rx_config_done = True




##
# @brief Process received status data (ACK, NACK,....)
#
# This process read status data (usually 3B) and do necessary process
#
# @param buffer_rx Received data
def Uni_process_rx_status_data(buffer_rx):
    global const_UNI_CHAR_ACK
    global const_UNI_CHAR_NACK
    global const_UNI_CHAR_RESET
    global const_UNI_CHAR_BUFFER_OVERFLOW
    
    global const_UNI_RES_CODE_CRC_ERROR
    global const_UNI_RES_CODE_ACK
    global const_UNI_RES_CODE_NACK
    global const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW
    global const_UNI_RES_CODE_RESET
    global const_UNI_RES_CODE_UNKNOWN_COMMAND
    
    # Set CRC to zero
    crc16 = 0
    
    # Test CRC first
    crc16 = crc_xmodem_update(crc16, buffer_rx[0])
    crc16 = crc_xmodem_update(crc16, buffer_rx[1])
    crc16 = crc_xmodem_update(crc16, buffer_rx[2])
    
    if(crc16 != 0):
        return const_UNI_RES_CODE_CRC_ERROR
    
    
    # Test for ACK
    if(buffer_rx[0] == const_UNI_CHAR_ACK):
        return const_UNI_RES_CODE_ACK
    
    # Test for NACK
    if(buffer_rx[0] == const_UNI_CHAR_NACK):
        return const_UNI_RES_CODE_NACK
    
    # Test for RESET
    if(buffer_rx[0] == const_UNI_CHAR_RESET):
        return const_UNI_RES_CODE_RESET
    
    # test for Buffer overflow from device
    if(buffer_rx[0] == const_UNI_CHAR_BUFFER_OVERFLOW):
        return const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW
    
    # If no status defined -> FAIL
    return const_UNI_RES_CODE_UNKNOWN_COMMAND


##
# @brief Try send data and return command code (ACK, NACK and so on)
def Uniprot_USB_try_tx_data( i_tx_data ):
    global device
    global s_packet_config
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL
    
    
    
    # Temporary buffer for TX data (8 Bytes)
    i_buffer_tx = [0x00]*8
    
    # Temporary buffer for RX data (8 Bytes)
    i_buffer_rx = [0x00]*8
    
    # CRC variable
    i_crc16 = 0
    
    # Index for i_tx_data
    i_tx_data_index = 0;
    
    # Load header to TX buffer
        # Header character
    i_buffer_tx[0] = const_UNI_CHAR_HEADER
    i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[0])
        # Number of data Bytes - H
    i_buffer_tx[1] = (s_packet_config.i_tx_num_of_data_Bytes>>8) & 0xFF
    i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[1])
        # Number of data Bytes - L
    i_buffer_tx[2] = (s_packet_config.i_tx_num_of_data_Bytes)    & 0xFF
    i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[2])
        # Data character
    i_buffer_tx[3] = const_UNI_CHAR_DATA
    i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[3])
    
    # Now calculate remaining data Bytes + Tail + CRC16
    i_tx_remain_data_Bytes = s_packet_config.i_tx_num_of_data_Bytes + 3
    # There is +3 because in real we must send tail plus CRC -> 3 Bytes
    
    i_buffer_tx_index = 4;
    
    
    # Send all remaining bytes
    while(i_tx_remain_data_Bytes >= 1):
        
        # Fill buffer_tx until is full or until i_tx_remain_data_Bytes >= 1
        while((i_tx_remain_data_Bytes >= 1) and (i_buffer_tx_index <8)):
            
            # Test if there are data - must remain more than 3 Bytes
            if(i_tx_remain_data_Bytes >= 4):
            # Data - load them to the buffer_tx
                i_buffer_tx[i_buffer_tx_index] = i_tx_data[i_tx_data_index]
                # Calculate CRC
                i_crc16 = \
                     crc_xmodem_update(i_crc16, i_buffer_tx[i_buffer_tx_index])
                # Increase index
                i_tx_data_index = i_tx_data_index + 1
            
            # Test if there is tail
            elif(i_tx_remain_data_Bytes == 3):
                # Add tail do TX buffer
                i_buffer_tx[i_buffer_tx_index] = const_UNI_CHAR_TAIL;
                # Calculate CRC
                i_crc16 = \
                    crc_xmodem_update(i_crc16, i_buffer_tx[i_buffer_tx_index])
            
            # Test if there is CRC High Byte
            elif(i_tx_remain_data_Bytes == 2):
                # Add CRC H to buffer
                i_buffer_tx[i_buffer_tx_index] = (i_crc16 >> 8) & 0xFF
                
            # Last option - CRC Low byte
            else:
                # Add CRC L to buffer
                i_buffer_tx[i_buffer_tx_index] = (i_crc16) & 0xFF
                
                
            # Increase index
            i_buffer_tx_index = i_buffer_tx_index + 1
            # Decrease i_remain_data_Bytes
            i_tx_remain_data_Bytes = i_tx_remain_data_Bytes - 1
        
        
        # If buffer i_buffer_tx is full, then
        # send data over USB and reset i_buffer_tx_index. However, if program
        # should send last byte (if condition) then is need to call
        # a different function and check ACK/NACK command
        
        if(i_tx_remain_data_Bytes <= 0):
            # Send last bytes
            usb_tx_data(device, i_buffer_tx)
            # Get command
            i_buffer_rx = usb_rx_data(device)

            status = Uni_process_rx_status_data(i_buffer_rx)
            print_if_debug_uniprot(status)
            # Return command status (ACK, NACK and so on)
            return status
        else:
            # Else just send another packet
            usb_tx_data(device, i_buffer_tx)
        
        # Anyway - clear some variables
        i_buffer_tx_index = 0
        
        # Load dummy data to buffer
        for i in range(8):
            i_buffer_tx[i] = 0xFF


##
# @brief Send data over USB
# @param i_tx_data Data, witch will be send
def Uniprot_USB_tx_data( i_tx_data ):

    global const_UNI_RES_CODE_CRC_ERROR
    global const_UNI_RES_CODE_ACK
    global const_UNI_RES_CODE_NACK
    global const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW
    global const_UNI_RES_CODE_RESET
    global const_UNI_RES_CODE_UNKNOWN_COMMAND
    global const_UNI_RES_CODE_DEVICE_NOT_FOUND
    
    status = Uniprot_USB_try_tx_data( i_tx_data )
    
    # Send data again if there is NACK or CRC ERROR
    while( (status == const_UNI_RES_CODE_NACK) or \
           (status == const_UNI_RES_CODE_CRC_ERROR)
         ):
        print_if_debug_uniprot("NACK or CRC error. TX data again...")
        status = Uniprot_USB_try_tx_data( i_tx_data )
    
    # Test for other options
    
    # Test for ACK
    if(status == const_UNI_RES_CODE_ACK):
        return const_UNI_RES_CODE_SUCCESS
    
    # Test for buffer overflow on device -> higher layer should solve this
    if(status == const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW):
        return const_UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW
    
    # Test for restart or unknown command
    if( (status == const_UNI_RES_CODE_RESET) or \
        (status == const_UNI_RES_CODE_UNKNOWN_COMMAND)
        ):
        # Restart device
        
        # Try close device
        Uniprot_close()
        
        # Try initialize device again
        if( Uniprot_init() != 0 ):
            # If reinitialization failed
            return const_UNI_RES_CODE_DEVICE_NOT_FOUND
        else:
            # Else reinitialization OK
            return const_UNI_RES_CODE_RESET
        
        
    # Program never should goes here (critical error)
    print("Uniprot_USB_tx_data: Unexpected internal error :( Exiting...")
    exit()


# @brief Send command over USB
# @param Command character (Example: const_UNI_CHAR_ACK)
def Uniprot_USB_tx_command( const_UNI_CHAR_CMD ):
    global device
    
    
    # Initialize crc16 value
    crc16 = 0
    
    # Fill buffer by zeros
    i_buffer_tx = [0x00]*8
    
    i_buffer_tx[0] = const_UNI_CHAR_CMD
    
    # Calculate CRC
    crc16 = crc_xmodem_update(crc16, const_UNI_CHAR_CMD)
    
    # And load crc16 value to TX buffer
    
    # CRC16 - MSB
    i_buffer_tx[1] = (crc16 >> 8) & 0xFF
    
    # CRC16 - LSB
    i_buffer_tx[2] = crc16 & 0xFF
    
    # Buffer is ready, send data
    usb_tx_data(device, i_buffer_tx)








##
# @brief Try receive data and return command code (ACK, NACK and so on)
def Uniprot_USB_try_rx_data():
    global device
    global s_packet_config
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL
    
    global i_buffer_rx

    
    
    # Temporary buffer for TX data (8 Bytes)
    i_buffer_tx = [0x00]*8
    
    # Temporary buffer for RX data
    i_buffer_rx_8 = [0x00]*8
    # Index for i_buffer_rx_8 - data begin at index 4 (index 0-3 is header)
    i_buffer_rx_8_index = 4;
    
    # Index for i_buffer_rx (user data)
    i_buffer_rx_index = 0;
    
    # Set CRC to zero
    crc16 = 0
    
    
    
    
    
    # RX first frame
    i_buffer_rx_8 = usb_rx_data(device)
    
    # Try to find header
    if((i_buffer_rx_8[0] == const_UNI_CHAR_HEADER) and
       (i_buffer_rx_8[3] == const_UNI_CHAR_DATA)):
        # If header is found save information about number of bytes (MSB first)
        s_packet_config.i_rx_num_of_data_Bytes =\
            (i_buffer_rx_8[1] << 8) + (i_buffer_rx_8[2])
        # Create RX buffer
        # RX buffer for data
        i_buffer_rx = [0x00]*(s_packet_config.i_rx_num_of_data_Bytes)
        
        # Calculate CRC
        crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[0])
        crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[1])
        crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[2])
        crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[3])
    else:
        # If correct header is not found, then return NACK 
        return const_UNI_RES_CODE_NACK
        
        
    
    # Calculate number of Bytes (include tail and CRC16 -> 3B -> +3)
    i_rx_remain_data_Bytes = s_packet_config.i_rx_num_of_data_Bytes + 3
    
    # Now save payload (data). RX all remaining bytes
    while(i_rx_remain_data_Bytes >= 1):
        # Process rest of data received by USB
        while((i_buffer_rx_8_index < 8) and (i_rx_remain_data_Bytes >= 1)):
            # If there are data
            if(i_rx_remain_data_Bytes >= 4):
                i_buffer_rx[i_buffer_rx_index] =\
                                            i_buffer_rx_8[i_buffer_rx_8_index]
                # Do CRC calculation
                crc16 = crc_xmodem_update(crc16,\
                                          i_buffer_rx_8[i_buffer_rx_8_index])
                # Increase both index
                i_buffer_rx_index   += 1
            
            # If there is Tail
            elif(i_rx_remain_data_Bytes == 3):
                # Check Tail itself
                if(i_buffer_rx_8[i_buffer_rx_8_index] == const_UNI_CHAR_TAIL):
                    # OK, Tail seems to be all right
                    crc16 = crc_xmodem_update(crc16, const_UNI_CHAR_TAIL)
                else:
                    # Else send NACK
                    return const_UNI_RES_CODE_NACK
            
            # Test CRC - high Byte
            elif(i_rx_remain_data_Bytes == 2):
                crc16 = crc_xmodem_update(crc16,\
                                          i_buffer_rx_8[i_buffer_rx_8_index])
            # Else CRC - low Byte
            else:
                crc16 = crc_xmodem_update(crc16,\
                                          i_buffer_rx_8[i_buffer_rx_8_index])
                # Test if CRC OK or not
            
            # Anyway, increase i_buffer_rx_8_index and decrease
            # i_rx_remain_data_Bytes
            i_buffer_rx_8_index    += 1
            i_rx_remain_data_Bytes -= 1
        # When jump out of previous loop -> read new data (if any remain)
        if(i_rx_remain_data_Bytes >= 1):
            # If there are still any data to receive -> get them!
            i_buffer_rx_8 = usb_rx_data(device)
        
        # Reset i_buffer_rx_8_index
        i_buffer_rx_8_index = 0
        
    # If all right -> return ACK -> higher layer should send ACK command
    return const_UNI_RES_CODE_ACK



##
# @brief Receive data over USB
# @return Received data as Byte stream
def Uniprot_USB_rx_data():
    global const_UNI_CHAR_ACK
    global const_UNI_CHAR_NACK
    global const_UNI_CHAR_RESET
    
    global i_buffer_rx
    
    status = Uniprot_USB_try_rx_data();
    print_if_debug_uniprot(">> Uniprot RX status (1): " + status)
    
    # Test status
    while(status != const_UNI_RES_CODE_ACK):
        # While is not ACK -> something is wrong -> try to do something!
        print_if_debug_uniprot(">> Uniprot RX status: " + status)
        
        # Test for NACK -> if NACK send all data again
        if(status == const_UNI_RES_CODE_NACK):
            # Send NACK to device
            Uniprot_USB_tx_command(const_UNI_CHAR_NACK)
            # And wait for data
            status = Uniprot_USB_try_rx_data()
        elif(status == const_UNI_RES_CODE_RESET):
            print ("Command RESET: Unfinished feature :( Exiting...")
            exit()
    
    # When ACK - previous while never run -> send ACK and return data
    Uniprot_USB_tx_command(const_UNI_CHAR_ACK)
   
    return i_buffer_rx