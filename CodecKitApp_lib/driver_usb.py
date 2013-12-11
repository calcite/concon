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


# Keyboard events (only debug for now)
#from msvcrt import kbhit


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
# packets)
const_USB_TIMEOUT_MS = 8

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
    
    for i in range(8):
        # Write from index 1 -> in index 0 is report_id 
        i_data_in[i] = data[i+1]
    
    # Print number in hex if in debug mode
    print_if_debug_usb_driver("+-------------------------------")
    for i in range(8):
       print_if_debug_usb_driver("| Udrv RX:{0}|{1}|{2}".format(i, hex(data[i+1]), str(unichr(data[i+1]))))







##
# @brief Open USB device. Should be called as first
#
# @param VID: Vendor ID
# @param PID: Product ID 
def usb_open_device(VID, PID):
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                     product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        device.open()
        print_if_debug_usb_driver("Device opened")
    except:
        # If not found
        print_if_debug_usb_driver("Device not found. Please make sure that device is connected")
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
        device.close()
        print_if_debug_usb_driver("Device closed")
        return 0
    except:
        # If not found
        print_if_debug_usb_driver("Device not found. Please make sure that\
             device is connected")
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
    
    timeout_cnt = const_USB_TIMEOUT_MS
    
    # Set last byte to value higher then 255 -> can receive only 0 - 255 ->
    # easy to detect, if all data were written is the check last "Byte"
    for i in range(8):
        i_data_in[i] = 512
    
    #set custom raw data handler
    device.set_raw_data_handler(in_sample_handler)
    
    # And wait until valid number will be received
    print_if_debug_usb_driver("\nW8 4 data")
    
    tmp = 0
    while ( (i_data_in[7] > 255) or\
            (i_data_in[6] > 255) or\
            (i_data_in[5] > 255) or\
            (i_data_in[4] > 255) or\
            (i_data_in[3] > 255) or\
            (i_data_in[2] > 255) or\
            (i_data_in[1] > 255) or\
            (i_data_in[0] > 255) ):  # Wait for valid data
    #while not kbhit() and device.is_plugged():    # Wait until pressed key
        sleep(0.001)
        # Instead of sleep function use simple counter
        tmp = tmp + 1
        if(tmp > timeout_cnt):
            print_if_debug_usb_driver("\n\n USB driver: RX timeout !!!")
            i_buffer_rx = [0xFF0]*8
            return i_buffer_rx
    
    print_if_debug_usb_driver("\nRX done")
    i_buffer_rx_cpy = list(i_data_in)
    
    # Load invalid data to original buffer -> specially for debug
    for i in range(8):
        i_data_in[i] = 0xFFF
    
    return i_buffer_rx_cpy




# << OLD FUNCTIONS >>


##
# @brief Send byte (8 Bytes) to device
#
# Example: tx_data_to_device_slow( data_send, 0x03EB, 0x204F )
def tx_data_to_device_slow( data_8bit, VID, PID ):
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                 product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        device.open()
        print_if_debug_usb_driver("Device opened")
        
    except:
        # If not found -> exception 
        print("Device not found. Please make sure that device is connected")
        return 404
    
    # Find OUT endpoint
    out_report = device.find_output_reports()[0]
    
    # Define buffer_tx ; 9 = report size (8 bits) + 1 byte (report id)
    buffer_tx= [0x00]*9        # Create and clear buffer_tx
    buffer_tx[0]=0x00          # report id
    
    print("+-------------------------------")
    for i in range(8):
        buffer_tx[i+1] = data_8bit[i]
        print_if_debug_usb_driver("| TX: {0}".format(hex(data_8bit[i])))
    
    # Send data in buffer_tx
    out_report.set_raw_data(buffer_tx)
    out_report.send()
    
    print_if_debug_usb_driver("Data send")
    
    # Close device
    device.close()
    print_if_debug_usb_driver("Device closed\n\n")
















##
# @brief Receive byte (8 Bytes) from device
#
# Example: data = rx_data_from_device_slow( 0x03EB, 0x204F )
def rx_data_from_device_slow( VID, PID ):
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                     product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        device.open()
        print_if_debug_usb_driver("Device opened")
    except:
        # If not found -> exception 
        print("Device not found. Please make sure that device is connected")
        return 404

    # Set i_data_in[0] to higher value than 255 (must be higher then 8 bit
    # maximum)
    global i_data_in
    i_data_in[0] = 512
    
    #set custom raw data handler
    device.set_raw_data_handler(in_sample_handler)
    
    # And wait until valid number will be received
    print_if_debug_usb_driver("W8 4 data")
    while i_data_in[0] > 255:  # Wait for valid data
    #while not kbhit() and device.is_plugged():    # Wait until pressed key
        sleep(0.0000000000002)
            
    print_if_debug_usb_driver("RX done")
      
    # Close device
    device.close()
    
    print_if_debug_usb_driver("Device closed\n\n")

    return i_data_in





##
# @brief Transmit 8 Bytes and then receive data from device
#
# Example: data_in = tx_rx_data_device_slow( data_tx, 0x03EB, 0x204F )
def tx_rx_data_device_slow(data_tx_8bit, VID, PID):
    # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                     product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        device.open()
        print_if_debug_usb_driver("Device opened")    
    
    except:
        # If not found -> exception 
        print("Device not found. Please make sure that device is connected")
        return 404
    
    # Find OUT endpoint
    out_report = device.find_output_reports()[0]
   
    # Define buffer_tx ; 9 = report size (8 bits) + 1 byte (report id)
    buffer_tx= [0x00]*9        # Create and clear buffer_tx
    buffer_tx[0]=0x00          # report id
    
    print("+-------------------------------")
    for i in range(8):
       buffer_tx[i+1] = data_tx_8bit[i]
       print_if_debug_usb_driver("| TX: {0}".format(hex(data_tx_8bit[i])))
    
    # Send data in buffer_tx
    out_report.set_raw_data(buffer_tx)
    out_report.send()
    
    print_if_debug_usb_driver("Data send")
    
    
    # Now receive data
    # Set i_data_in[0] to higher value than 255 (must be higher then 8 bit
    # maximum)
    global i_data_in
    i_data_in[0] = 512
    
    #set custom raw data handler
    device.set_raw_data_handler(in_sample_handler)
    
    # And wait until valid number will be received
    print_if_debug_usb_driver("W8 4 data")
    while i_data_in[0] > 255:  # Wait for valid data
    #while not kbhit() and device.is_plugged():    # Wait until pressed key
        sleep(0.02)
            
    print_if_debug_usb_driver("RX done")
      
    # Close device
    device.close()
    
    print_if_debug_usb_driver("Device closed\n\n")

    return i_data_in



##
# @brief Receive 8 Bytes and then transmit data to device
#
# Example: data_in = rx_tx_data_device_slow( data_tx, 0x03EB, 0x204F )
def rx_tx_data_device_slow(data_tx_8bit, VID, PID):
        # Try open device
    try:
        device = hid.HidDeviceFilter(vendor_id = VID,
                                     product_id = PID).get_devices()[0]
        print_if_debug_usb_driver("Device found")
        device.open()
        print_if_debug_usb_driver("Device opened")    
    
    except:
        # If not found -> exception 
        print("Device not found. Please make sure that device is connected")
        return 404
    
    
    
    # Set i_data_in[0] to higher value than 255 (must be higher then 8 bit
    # maximum)
    global i_data_in
    i_data_in[0] = 512
    
    #set custom raw data handler
    device.set_raw_data_handler(in_sample_handler)
    
    # And wait until valid number will be received
    print_if_debug_usb_driver("W8 4 data")
    while i_data_in[0] > 255:  # Wait for valid data
    #while not kbhit() and device.is_plugged():    # Wait until pressed key
        sleep(0.02)
            
    print_if_debug_usb_driver("RX done")
    
    
    
    
    # Find OUT endpoint
    out_report = device.find_output_reports()[0]
    
    # Define buffer_tx ; 9 = report size (8 bits) + 1 byte (report id)
    buffer_tx= [0x00]*9        # Create and clear buffer_tx
    buffer_tx[0]=0x00          # report id
    
    print("+-------------------------------")
    for i in range(8):
        buffer_tx[i+1] = data_8bit[i]
        print_if_debug_usb_driver("| TX: {0}".format(hex(data_8bit[i])))
    
    # Send data in buffer_tx
    out_report.set_raw_data(buffer_tx)
    out_report.send()
    
    print_if_debug_usb_driver("Data send")
    
    # Close device
    device.close()
    print_if_debug_usb_driver("Device closed\n\n")
    
    return i_data_in
    