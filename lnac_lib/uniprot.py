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

const_UNI_RES_CODE_CRC_ERROR = "CRC ERROR"

const_UNI_RES_CODE_ACK_OK = "ACK OK"
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
s_packet_config = UNI_PACKET_CONFIG()

s_status        = UNI_STATUS()

device = 404
# @}




##
# @brief Print message only if version is debug
def print_if_debug( string ):
    if const_uniprot_VERSION() == "debug":
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
    global const_UNI_CRC_ERROR
    global const_UNI_RES_CODE_ACK_OK
    
    # Set CRC to zero
    crc16 = 0
    
    # Test for ACK
    if(buffer_rx[0] == const_UNI_CHAR_ACK):
        # If ACK, then check CRC - just for case
        crc16 = crc_xmodem_update(crc16, buffer_rx[0])
        crc16 = crc_xmodem_update(crc16, buffer_rx[1])
        crc16 = crc_xmodem_update(crc16, buffer_rx[2])
        
        if(crc16 != 0):
            return "CRC ERROR (ACK)"
        else:
            return "ACK"
    
    # Test for NACK
    if(buffer_rx[0] == const_UNI_CHAR_NACK):
        # If NACK, then check CRC
        crc16 = crc_xmodem_update(crc16, buffer_rx[0])
        crc16 = crc_xmodem_update(crc16, buffer_rx[1])
        crc16 = crc_xmodem_update(crc16, buffer_rx[2])
        
        if(crc16 != 0):
            return "CRC ERROR (NACK)"
        else:
            return "NACK"
        
    
    # Test for RESET
    if(buffer_rx[0] == const_UNI_CHAR_RESET):
        # If NACK, then check CRC
        crc16 = crc_xmodem_update(crc16, buffer_rx[0])
        crc16 = crc_xmodem_update(crc16, buffer_rx[1])
        crc16 = crc_xmodem_update(crc16, buffer_rx[2])
        
        if(crc16 != 0):
            return "CRC ERROR (RESET)"
        else:
            return "RESET"
    
    # If no status defined -> FAIL
    return "ERROR: Unknown status"


##
# @brief Send data over USB
# @param i_tx_data Data, witch will be send
def Uniprot_USB_tx_data( i_tx_data ):
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
        
        
        # If buffer i_buffer_tx is full, or i_tx_remain_data_Bytes <= 0 then
        # send data over USB and reset i_buffer_tx_index. However, if program
        # should send last byte (if condition) then is need to call
        # a different function and check ACK/NACK command
        
        if((i_buffer_tx_index < 8) or (i_tx_remain_data_Bytes <= 0)):
            usb_tx_data(device, i_buffer_tx)
            i_buffer_rx = usb_rx_data(device)

            status = Uni_process_rx_status_data(i_buffer_rx)
            # @todo: Process ACK, NACK and so on
            print(status)
        else:
            usb_tx_data(device, i_buffer_tx)
        
        # Anyway - clear some variables
        i_buffer_tx_index = 0
        
        # Load dummy data to buffer
        for i in range(8):
            i_buffer_tx[i] = 0xFF



# @brief Send command over USB
# @param Command character (Example: const_UNI_CHAR_ACK)
def Uniprot_USB_tx_command( const_UNI_CHAR_CMD ):
    global device
    
    const_UNI_CHAR_CMD = ord(const_UNI_CHAR_CMD)
    
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
# @brief Send data over USB
# @param i_tx_data Data, witch will be send
def Uniprot_USB_rx_data():
    global device
    global s_packet_config
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL

    
    # Temporary buffer for TX data (8 Bytes)
    i_buffer_tx = [0x00]*8
    
    # Temporary buffer for RX data
    i_buffer_rx = 0x00
    
    # Set CRC to zero
    crc16 = 0
    
    # Index for i_rx_data
    i_rx_data_index = 0;
    
    
    for i in range(6):
        i_buffer_rx = usb_rx_data(device)
        for j in range(8):
            print("RXD {0} | {1}".format(hex(i_buffer_rx[j]), str(unichr(i_buffer_rx[j])) ))
        print("<<---------->>")
    