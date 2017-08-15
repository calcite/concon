# -*- coding: utf-8 -*-

import yaml
# from ConfigParser import *
# For detection python version (2 or 3)
from usb_driver import UsbDriver


class SupportedDevices(list):
    """ Manage supported devices (VIDs, PIDs).
    """

    def __init__(self, config_file=None):
        list.__init__(self)
        self.vid_list = []
        self.pid_ignore_list = []
        if config_file:
            self.load_from_config(config_file)

    def load_from_config(self, config_file):
        """ Load supported devices IDs (VIDs, PIDs) from a configuration file.
        """
        with file(config_file) as cf:
            config = yaml.load(cf)
            self.vid_list = config['devices']['supported-vids']
            self.pid_ignore_list = config['devices']['ignored-pids']

    def get_connected_devices(self):
        """ Enlist all connected supported devices."""
        all_devices = []
        if self.vid_list:
            for vid in self.vid_list:
                all_devices += UsbDriver.usb_list_devices(vid)

        if self.pid_ignore_list:
            return [device for device in all_devices
                    if not (device.product_id in self.pid_ignore_list)]
        else:
            return all_devices

# Example of using this library

# # Read supported devices list from file
#device_list = SupportedDevices.create_from_config_file(filename)

# # Define list of supported devices manually
#device_list = [DeviceStruct("CodecKit", 0x023, 0x204f),
#                                DeviceStruct()])
