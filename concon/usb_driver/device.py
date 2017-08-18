"""
.. module:: usb_driver.device
    :platform: Unix, Windows
    :synopsis: Classes for description of connected devices
.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>
.. moduleauthor:: Josef Nevrly <jnevrly@alps.cz>

"""
from .driver import UsbDriver, UsbDriverException


class UsbDeviceException(UsbDriverException):
    pass


class UsbDevice:
    """ Basic structure for every device. Encapsulates different USB HID
    controls on Linux or Windows systems.
    """

    def __init__(self, name, vid, pid, uid, timeout=UsbDriver.USB_TIMEOUT_MS):
        self.name = name
        self.vid = vid
        self.pid = pid
        self.uid = uid
        self._driver = UsbDriver(timeout=timeout)
        self.usb_device = None

    def __str__(self):
        return " Device name: {0}\n VID: {1}\n PID: {2}, UID: {3}\n-------\n" \
               "".format(self.name, hex(self.vid), hex(self.pid), hex(self.uid))

    def _check_device_open(self):
        if self.usb_device is None:
            raise UsbDriverException("Device not opened.")

    def ping(self):
        """ Just test if selected device is connected.
        """
        return UsbDriver.usb_ping_device(self.vid, self.pid)

    def open(self, timeout=UsbDriver.USB_TIMEOUT_MS):
        """ Open USB device. Should be called first"""
        self._driver = UsbDriver(timeout=timeout)
        self.usb_device = self._driver.usb_open_device(self.vid, self.pid)
        return self.usb_device

    def close(self):
        """ Close USB device. Should be called last."""
        self._check_device_open()
        tmp = UsbDriver.usb_close_device(self.usb_device)
        self.usb_device = None
        return tmp

    def tx_data(self, data_8bit):
        """ Send data (64 bits per 8 bits) over USB interface

        :param data_8bit: Data to TX (8 bytes -> 64 bits)
        :type data_8bit: List of 8 bit data values
        """
        self._check_device_open()
        return self._driver.usb_tx_data(self.usb_device, data_8bit)

    def rx_data(self):
        """ Receive data from USB interface (8x8bits)
        """
        self._check_device_open()
        return self._driver.usb_rx_data(self.usb_device)

