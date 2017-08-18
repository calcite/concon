# -*- coding: utf-8 -*-
"""
.. module:: concon.supported_devices
    :synopsis: Representation of supported devices recognized by concon.

.. moduleauthor:: Josef Nevrly <jnevrly@alps.cz>
.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>

"""

from .usb_driver import UsbDriver


class SupportedDevices(list):
    """ Manage supported devices (VIDs, PIDs).
    """

    def __init__(self, supported_vids=[], ignored_pids=[]):
        list.__init__(self)
        self.vid_list = supported_vids
        self.pid_ignore_list = ignored_pids

    # @classmethod
    # def load_from_config(self, config_file):
    #     """ Load supported devices IDs (VIDs, PIDs) from a configuration file.
    #     """
    #     with file(config_file) as cf:
    #         config = yaml.load(cf)
    #         self.vid_list = config['devices']['supported_vids']
    #         self.pid_ignore_list = config['devices']['ignored_pids']

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
