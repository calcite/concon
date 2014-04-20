#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USB driver. Use pywinusb and pyusb according to actual OS
#
# Author: Martin Stejskal

# For adding system paths
import sys

# Allow detect operating system
import os

# Add usb_driver_lib to path
sys.path.append("usb_driver_lib")

from usb_driver_lib import *


##
# @brief "Constants"
# @{

##
# @brief Define maximum time in which must data came back from device
#
# Note that usually there is not problem on device side, but on PC side\n
# (depend on CPU load -> application process time -> sometimes can miss\n
# packets). So there is some timeout so application will not hang on.
# However this problem is usually occurs on Windows (pywinusb implementation) 
const_USB_TIMEOUT_MS = 50


##
# @}


##
# @brief Global variables
# @{

# To this variable is stored name of operating system
detected_os = None

# When auto initialize process is done, this variable is set to 1
initialized = 0





def usb_ping_device(VID, PID):
  """
  Just test if selected device is connected
  
  :param VID: VendorID
  :type VID: 16 bit number
  :param PID: ProductID
  :type PID: 16 bit number
  """
  # Call function which ping device
  return usb_lib_ping_device(VID, PID)




def usb_open_device(VID, PID):
  """
  Open USB device. Should be called as first
  
  :param VID: VendorID
  :type VID: 16 bit number
  :param PID: ProductID
  :type PID: 16 bit number
  """
  return usb_lib_open_device(VID, PID)



def usb_close_device(device):
  """
  Close USB device. Should be called as last
  :param device: device object
  """
  return usb_lib_close_device(device)



def usb_tx_data(device, data_8bit):
  """
  Send data (64 bits per 8 bits) over USB interface
  
  :param device: device description, witch programmer get when use function
   usb_open_device
  :param data_8bit: Data to TX (8 bytes -> 64 bits)
  :type data_8bit: List of 8 bit data values
  """
  return usb_lib_tx_data(device, data_8bit)


def usb_rx_data(device):
  """
  Receive data from USB interface (8x8bits)
  
  :param device: Device description, witch programmer get when use function
   usb_open_device
  """
  global const_USB_TIMEOUT_MS
  
  return usb_lib_rx_data(device, const_USB_TIMEOUT_MS)

