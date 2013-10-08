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
const_VERSION = "release"

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

# @}


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
            return "CRC ERROR"
        else:
            return "ACK"
    
    
    # If no status defined -> FAIL
    return "ERROR: Unknown status"

##
# @brief Load data from tx_buffer and send them over USB
def Uniprot_USB_tx_load_data_from_buffer( i_DataArray,
                                          i_DataArray_index,
                                          i_rx_remain_data_Bytes,
                                          crc16 ):
    print("NOP")

##
# @brief Send data over USB
# @param i_tx_data Data, witch will be send
def Uniprot_USB_tx_data( i_tx_data ):
    global s_packet_config
    global const_UNI_CHAR_HEADER
    global const_UNI_CHAR_DATA
    global const_UNI_CHAR_TAIL
    global const_USB_VID
    global const_USB_PID
    
    # Temporary buffer for TX data (8 Bytes)
    buffer_tx = [0x00]*8
    
    # Temporary buffer for RX data (8 Bytes)
    buffer_rx = [0x00]*8
    
    # CRC variable
    crc16 = 0
    
    
    # Load header to TX buffer
        # Header character
    buffer_tx[0] = const_UNI_CHAR_HEADER
    crc16 = crc_xmodem_update(crc16, buffer_tx[0])
        # Number of data Bytes - H
    buffer_tx[1] = (s_packet_config.i_tx_num_of_data_Bytes>>8) & 0xFF
    crc16 = crc_xmodem_update(crc16, buffer_tx[1])
        # Number of data Bytes - L
    buffer_tx[2] = (s_packet_config.i_tx_num_of_data_Bytes)    & 0xFF
    crc16 = crc_xmodem_update(crc16, buffer_tx[2])
        # Data character
    buffer_tx[3] = const_UNI_CHAR_DATA
    crc16 = crc_xmodem_update(crc16, buffer_tx[3])
    
    # Now calculate remaining data Bytes + Tail + CRC16
    i_rx_remain_data_bytes = s_packet_config.i_tx_num_of_data_Bytes + 3
    # There is +3 because in real we must send tail plus CRC -> 3 Bytes
    
    
    # If remaining length will be exactly 3 -> all can be saved to one USB
    # transmission (just add tail and CRC)
    if(i_rx_remain_data_bytes == 3):
        # Tail
        buffer_tx[4] = const_UNI_CHAR_TAIL
        crc16 = crc_xmodem_update(crc16, buffer_tx[4])
        # And add CRC
        buffer_tx[5] = crc16>>8
        buffer_tx[6] = crc16 & 0xFF
        
        # Send data and receive status (ACK/NACK and so on)
        buffer_rx = tx_rx_data_device( buffer_tx,\
                                       const_USB_VID,\
                                       const_USB_PID)
        status = Uni_process_rx_status_data(buffer_rx)
        print(status);
    else:
        print("We got a problem")
    
    # Clear TX buffer
    #for b in buffer_tx:
    #    b = 0x00
    #    print(b)
        
        