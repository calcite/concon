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



class DeviceStruct():
  """
  Basic structure for every device
  """
  def __init__(self, name, vid, pid):
    self.name = name
    self.vid = vid
    self.pid = pid

  def __str__(self):
    return " Device name: {0}\n VID: {1}\n PID: {2}\n---------------------\n"\
    "".format(self.name, hex(self.vid), hex(self.pid))


class SupportedDevices(list):
  @classmethod
  def create_from_config_file(cls, config_file):
    devices = cls()
    cfg = RawConfigParser()
    cfg.read(config_file)
    # Read number of devices
    num_of_dev = cfg.getint("NumOfDev", "num_of_dev")
    
    for i in range(num_of_dev):
      devices.append(DeviceStruct(cfg.get(str(i), "name"), 
                                  int(cfg.get(str(i), "vid"), 16),
                                  int(cfg.get(str(i), "pid"), 16)  ))
    #parse file to devices
    return devices
  
  def __init__(self):
    list.__init__(self)
    

# Example of using this library

# # Read supported devices list from file
#device_list = SupportedDevices.create_from_config_file(filename)

# # Define list of supported devices manually
#device_list = [DeviceStruct("CodecKit", 0x023, 0x204f),
#                                DeviceStruct()])
