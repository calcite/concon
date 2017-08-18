"""
.. module:: concon.usb_driver.driver
    :platform: Unix, Windows
    :synopsis: Classes for description of connected devices

.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>
.. moduleauthor:: Josef Nevrly <jnevrly@alps.cz>

"""
import os
import yaml
from ..utils import ConConError

if os.name == "posix":
    from .linux import *
elif os.name == "nt":
    from .windows import *
else:
    raise Exception("Unsupported OS")


class UsbDriverException(ConConError):
    pass


class UsbDriver:

    USB_TIMEOUT_MS = 700
    """ Maximum time in which must data came back from device. Note that 
    usually there is not problem on device side, however timeout must
    calculate with data processing on device side and PC side. 
    Higher value is better (device can process more data meanwhile
    PC wait for response), but in case that some data are lost, 
    data throughput will be decreased. So set this value wisely.
    """

    def __init__(self, timeout=USB_TIMEOUT_MS):
        self._timeout = timeout

    @classmethod
    def init_from_config(cls, config_file):
        return cls(timeout=cls.get_config_from_file(config_file)['timeout'])

    @classmethod
    def get_config_from_file(cls, config_file):
        with file(config_file) as cf:
            config = yaml.load(cf)
            return config['usb']

    @classmethod
    def usb_ping_device(cls, vid, pid):
        """
        Just test if selected device is connected

        :param vid: VendorID
        :type vid: 16 bit number
        :param pid: ProductID
        :type pid: 16 bit number
        """
        # Call function which ping device
        return usb_lib_ping_device(vid, pid)

    @classmethod
    def usb_open_device(cls, vid, pid):
        """
        Open USB device. Should be called as first

        :param vid: VendorID
        :type vid: 16 bit number
        :param pid: ProductID
        :type pid: 16 bit number
        """
        return usb_lib_open_device(vid, pid)


    @classmethod
    def usb_close_device(cls, device):
        """
        Close USB device. Should be called as last
        :param device: device object
        """
        return usb_lib_close_device(device)

    def usb_tx_data(self, device, data_8bit):
        """
        Send data (64 bits per 8 bits) over USB interface

        :param device: device description, witch programmer get
                       when use function usb_open_device
        :param data_8bit: Data to TX (8 bytes -> 64 bits)
        :type data_8bit: List of 8 bit data values
        """
        return usb_lib_tx_data(device, data_8bit, self._timeout)

    def usb_rx_data(self, device):
        """
        Receive data from USB interface (8x8bits)

        :param device: Device description, witch programmer get when use
                        function usb_open_device
        """

        return usb_lib_rx_data(device, self._timeout)

    @classmethod
    def usb_list_devices(cls, vid=None):
        from .device import UsbDevice
        """
        List all connected devices, optionally filter only devices
        with given Vendor ID.
        
        :param vid:    (Optional) Vendor ID.
        
        :return: List of connected devices (DeviceStructs).
        """
        return [UsbDevice(*dev) for dev in usb_list_connected_devices(vid)]

