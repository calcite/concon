#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USB driver for Windows
#
# Author: Martin Stejskal


# Use pyWinUSB library for python and use shortcut "hid"
import pywinusb.hid as hid

# Queue - FIFO/LIFO memory for multi-thread applications
import Queue



# Queue object
rx_buff = None



def in_sample_handler(data):
  """
  Callback function for "set_raw_data_handler"
  
  :param data: Raw data
  :type data: 8 bit values
  """
  # Write data to global variable
  global rx_buff
  # Save data
  rx_buff.put(data, 1)



def usb_lib_ping_device(VID, PID):
  """
  Just test if selected device is connected
  
  :param VID: VendorID
  :type VID: 16 bit number
  :param PID: ProductID
  :type PID: 16 bit number
  """
  try:
    tmp_device = hid.HidDeviceFilter(vendor_id = VID, product_id = PID).get_devices()[0]
    # If we open device, we must close it!
    tmp_device.close()
    # If device exist
    return 1;
  except:
    # Device not exist
    return 404



def usb_lib_open_device(VID, PID):
  """
  Open USB device. Should be called as first
  
  :param VID: VendorID
  :type VID: 16 bit number
  :param PID: ProductID
  :type PID: 16 bit number
  """
  global rx_buff
  
  # Try open device
  try:
      device = hid.HidDeviceFilter(vendor_id = VID,
                                   product_id = PID).get_devices()[0]
      device.open()
      
      # set custom raw data handler if device is opened
      device.set_raw_data_handler(in_sample_handler)
  except:
      # If not found
      device = 404
  # OK, device opened. So use queue FIFO buffer. Size is 256 [objects]
  rx_buff = Queue.Queue(256)
  return device



def usb_lib_close_device(device):
  """
  Close USB device. Should be called as last
  :param device: device object
  """
  # Try close device
  try:
      device.close()
      return 0
  except:
      # If not found
      return 404



def usb_lib_tx_data(device, data_8bit):
  """
  Send data (64 bits per 8 bits) over USB interface
  
  :param device: device description, witch programmer get when use function
   usb_open_device
  :param data_8bit: Data to TX (8 bytes -> 64 bits)
  :type data_8bit: List of 8 bit data values
  """
  # Find OUT endpoint
  out_report = device.find_output_reports()[0]
  
  # Define buffer_tx ; 9 = report size (8 bits) + 1 byte (report id)
  buffer_tx= [0x00]*9        # Create and clear buffer_tx
  buffer_tx[0]=0x00          # report id
  
  for i in range(8):
      buffer_tx[i+1] = data_8bit[i]
  
  # Send data in buffer_tx
  out_report.set_raw_data(buffer_tx)
  out_report.send()
  
  return 0




def usb_lib_rx_data(device, timeout):
  """
  Receive data from USB interface (8x8bits)
  
  :param device: Device description, witch programmer get when use function
   usb_open_device
  """
  global rx_buff
  
  data = [0x00]*8
  
  # OK, try to get data
  try:
    data = rx_buff.get(1, (timeout*0.001))
  except:
    # Timeout
    data = [0xFF0]*8
    return data
  
  # Else data OK -> return them
  return data[1:]
