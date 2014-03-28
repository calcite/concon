##
# @file
#
# @brief Driver for USB Generic HID device 
#
# @author Martin Stejskal

# Use pyWinUSB library for python and use shortcut "hid"
import pywinusb.hid as hid

# Time operations
from time import sleep

# Threading
import threading


##
# @brief "Constants"
# @{
    # options: debug, release
const_USB_DRV_VERSION = "release"
#const_USB_DRV_VERSION = "debug"

##
# @brief Define maximum time in which must data came back from device
#
# Note that usually there is not problem on device side, but on PC side\n
# (depend on CPU load -> application process time -> sometimes can miss\n
# packets). Value 0 set timeout to infinity (Useful only for debug)
const_USB_TIMEOUT_MS = 8
#const_USB_TIMEOUT_MS = 0

##
# @}




##
# @brief Global variables
# @{

##
# @brief For data from device
# When receiving data from device it is called function, that fill this\n
# global variable
i_data_in = [0x00]*8

##
# @brief For semaphore blocking - for now value is None
event = None



##
# @brief Print message only if version is debug
def print_if_debug_usb_driver( string ):
    global const_USB_DRV_VERSION
    
    if(const_USB_DRV_VERSION == "debug"):
        print( string )

##
# @brief Callback function for "set_raw_data_handler"
def in_sample_handler(data):
    # Write data to global variable
    global i_data_in
    # Need to copy data, not just point to them"
    i_data_in = data[1:]
    
    # Unlock 
    event.set()
"""
    
    for i in range(8):
        # Write from index 1 -> in index 0 is report_id 
        i_data_in[i] = data[i+1]
    
    # Print number in hex if in debug mode
    print_if_debug_usb_driver("+-------------------------------")
    for i in range(8):
       print_if_debug_usb_driver("| Udrv RX:{0}|{1}|{2}".format(
                                                          i,
                                                          hex(data[i+1]),
                                                          unichr(data[i+1])))
"""






##
# @brief Open USB device. Should be called as first
#
# @param VID: Vendor ID
# @param PID: Product ID 
def usb_open_device(VID, PID):
    global event
    
    # Prepare semaphore
    event = threading.Event()
    # Clear - for now block RX data
    event.clear()
    
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                     product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        device.open()
        print_if_debug_usb_driver("Device opened")
        
        # set custom raw data handler if device is opened
        device.set_raw_data_handler(in_sample_handler)
    except:
        # If not found
        print_if_debug_usb_driver("Device not found."
                                  " Please make sure that device is connected")
        device = 404
    return device

##
# @brief Close USB device. Should be called as last
#
# @param VID: Vendor ID
# @param PID: Product ID 
def usb_close_device(VID, PID):
    # Try close device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                     product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        # Clear handler
        device.set_raw_data_handler(None)
        
        device.close()
        print_if_debug_usb_driver("Device closed")
        return 0
    except:
        # If not found
        print_if_debug_usb_driver("Device not found. Please make sure that"
                                  " device is connected")
        return 404


##
# @brief Send data (64 bits per 8 bits) over USB interface
#
# @param device: device description, witch programmer get when use \n
# function usb_open_device
# @param data_8bit: array of 8 bit values (only 64 bit will be transmitted)
def usb_tx_data(device, data_8bit):
    # Find OUT endpoint
    out_report = device.find_output_reports()[0]
    
    # Define buffer_tx ; 9 = report size (8 bits) + 1 byte (report id)
    buffer_tx= [0x00]*9        # Create and clear buffer_tx
    buffer_tx[0]=0x00          # report id
    
    print_if_debug_usb_driver("+-------------------------------")
    for i in range(8):
        buffer_tx[i+1] = data_8bit[i]
        print_if_debug_usb_driver("| TX: {0}".format(hex(data_8bit[i])))
    
    # Send data in buffer_tx
    out_report.set_raw_data(buffer_tx)
    out_report.send()
    
    print_if_debug_usb_driver("Data send")

##
# @brief Receive data from USB interface (8x8bits)
#
# @param device: device description, witch programmer get when use \n
# function usb_open_device

def usb_rx_data(device):
    global i_data_in
    global const_USB_TIMEOUT_MS
    
    
    
    # Reset counter
    cnt = 0
    # Wait for data
    while(1):
      # Wait 1ms, or less
      event.wait(0.001)
      
      # Check if data received
      if(True == event.isSet()):
        # Lock again
        event.clear()
        # If flag is set -> break
        break
      
      cnt = cnt +1
      if((cnt > const_USB_TIMEOUT_MS) and (const_USB_TIMEOUT_MS != 0)):
        print_if_debug_usb_driver("USB RX timeout!")
        i_buffer_rx = [0xFF0]*8
        # Lock again (for case, that "now" data comes)
        event.clear()
        
        return i_buffer_rx
    
    return i_data_in

