#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
#
# @brief CRC XMODEM algorithm
#
# Same algorithm as used for AVR in library <util/crc16.h>
#
# @author Martin Stejskal
#


##
# @brief Calculate CRC for 1 byte
#
# Polynomial: x^16 + x^12 + x^5 + 1 (0x1021)
# Initial value: 0x0
# Example: crc_xmodem_update( crc, 0x34 )
#
# @param crc: 16 bit CRC value
# @param data: 8 bit data value
def crc_xmodem_update( crc, data):
    # crc must not be higher than 16 bits
    crc = 0xFFFF & crc
    
    # data must not be higher than 8 bits
    data = 0xFF & data
    
    crc = crc ^ (data << 8)
    for i in range(8):
        if (crc & 0x8000):
            crc = (crc << 1) ^ 0x1021
        else:
            crc = crc << 1
            
    # Return only 16 bits
    return (0xFFFF & crc)