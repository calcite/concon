#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USB driver. Use pywinusb and pyusb according to actual OS
#
# Author: Martin Stejskal

import commentjson
from usb_driver_lib import *

##
# @brief "Constants"
# @{

##
# @brief Define maximum time in which must data came back from device
#
# Note that usually there is not problem on device side, however timeout must
# calculate with data processing on device side and PC side. Higher value
# is better (device can process more data meanwhile PC wait for response),
# but in case that some data are lost, data throughput will be decreased. So
# set this value wisely
const_USB_TIMEOUT_MS = 700

##
# @}


##
# @brief Global variables
# @{

# To this variable is stored name of operating system
detected_os = None

# When auto initialize process is done, this variable is set to 1
initialized = 0


def usb_load_config(config_file):
    global const_USB_TIMEOUT_MS

    with file(config_file) as cf:
        config = commentjson.load(cf)
        const_USB_TIMEOUT_MS = config['USB_timeout']


def usb_ping_device(vid, pid):
    """
    Just test if selected device is connected
    
    :param vid: VendorID
    :type vid: 16 bit number
    :param pid: ProductID
    :type pid: 16 bit number
    """
    # Call function which ping device
    return usb_lib_ping_device(vid, pid)


def usb_open_device(vid, pid):
    """
    Open USB device. Should be called as first
    
    :param vid: VendorID
    :type vid: 16 bit number
    :param pid: ProductID
    :type pid: 16 bit number
    """
    return usb_lib_open_device(vid, pid)


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
    global const_USB_TIMEOUT_MS
    return usb_lib_tx_data(device, data_8bit, const_USB_TIMEOUT_MS)


def usb_rx_data(device):
    """
    Receive data from USB interface (8x8bits)
    
    :param device: Device description, witch programmer get when use function
     usb_open_device
    """
    global const_USB_TIMEOUT_MS

    return usb_lib_rx_data(device, const_USB_TIMEOUT_MS)


def usb_list_devices(vid=None):
    """
    List all connected devices, optionally filter only devices with given Vendor ID.
    
    :param vid:    (Optional) Vendor ID.
    
    :return: List of connected devices (DeviceStructs).
    """
    return usb_list_connected_devices(vid)
