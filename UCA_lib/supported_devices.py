# -*- coding: utf-8 -*-

##
# In this file is simple list of supported devices for UniversalControlApp

#from ConfigParser import *
# For detection python version (2 or 3)
import sys
if(sys.version_info[0] == 2):
  from ConfigParser import *
elif(sys.version_info[0] == 3):
  import configparser as ConfigParser
  from configparser import *

from usb_driver_lib.device import DeviceStruct
from usb_driver import usb_list_devices
import commentjson

class SupportedDevices(list):

    def __init__(self, config_file=None):
        list.__init__(self)
        vid_list = []
        pid_ignore_list = []
        if config_file:
            self.load_from_config(config_file)
        
    def load_from_config(self, config_file):  
        with file(config_file) as cf:
            config = commentjson.load(cf)
            self.vid_list = config['Supported_VID']
            self.pid_ignore_list = config['Ignored_PID']
    
    def get_connected_devices(self):
        all_devices = []
        if self.vid_list:
            for vid in self.vid_list:
                all_devices += usb_list_devices(vid)
                
        if self.pid_ignore_list:
            return [device for device in all_devices \
                    if not (device.product_id in self.pid_ignore_list)]
        else:
            return all_devices

# Example of using this library

# # Read supported devices list from file
#device_list = SupportedDevices.create_from_config_file(filename)

# # Define list of supported devices manually
#device_list = [DeviceStruct("CodecKit", 0x023, 0x204f),
#                                DeviceStruct()])
