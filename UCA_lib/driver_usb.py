##
# @file
#
# @brief Driver for USB Generic HID device 
#
# @author Martin Stejskal

# Use pyWinUSB library for python and use shortcut "hid"
import pywinusb.hid as hid

# Queue - FIFO/LIFO memory for multi-thread applications
import Queue


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
# packets). So there is some timeout so application will not hang on.
const_USB_TIMEOUT_MS = 50

##
# @}


##
# @brief Global variables
# @{

# Queue object
rx_buff = None



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
    global rx_buff
    # Save data
    rx_buff.put(data, 1)



##
# @brief Just test if selected device is connected
# @param VID: Vendor ID
# @param PID: Product ID 
def usb_ping_device(VID, PID):
  try:
    hid.HidDeviceFilter(vendor_id = VID, product_id = PID).get_devices()[0]
    # If device exist
    return 1;
  except:
    # Device not exist
    return 404

##
# @brief Open USB device. Should be called as first
#
# @param VID: Vendor ID
# @param PID: Product ID 
def usb_open_device(VID, PID):
    global rx_buff
    
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
    # OK, device opened. So use queue FIFO buffer. Size is 256 [objects]
    rx_buff = Queue.Queue(256)
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
    global const_USB_TIMEOUT_MS
    global rx_buff
    
    data = [0x00]*8
    
    # OK, try to get data
    try:
      data = rx_buff.get(1, (const_USB_TIMEOUT_MS*0.001))
    except:
      # Timeout
      print_if_debug_usb_driver("USB RX timeout!")
      data = [0xFF0]*8
      return data
    
    # Else data OK -> return them
    return data[1:]

