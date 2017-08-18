# -*- coding: utf-8 -*-

from .supported_devices import SupportedDevices
from .usb_driver import UsbDriver
from .utils import ConConError
import pkg_resources
import logging
import logging.config
import yaml
from collections import OrderedDict
from .bridge_config_parser import BridgeConfigParser

DEFAULT_CONFIG = 'config/config.yml'

logger = logging.getLogger(__name__)


class ConCon(object):
    """ Representation of Configured device."""

    def __init__(self, config=None):
        #
        try:
            if config is None:
                conf_file = pkg_resources.resource_filename('concon',
                                                            DEFAULT_CONFIG)

                with open(conf_file, 'r') as cf:
                    config = yaml.load(cf)

        except OSError as e:
            msg = " Invalid file path or configuration file: {0}!\n".format(
                str(e))
            logger.error("[SupportedDevices]" + msg)

        self._config = config

    def get_device_list(self):
        """
        :return: List of :class:`~concon.core.ConConDevice` sorted
                    alphabetically by the device name.
        """
        devices = SupportedDevices(**self._config['devices'])
        usb = UsbDriver(timeout=self._config['usb']['timeout'])
        dev_list = devices.get_connected_devices()

        # Now try to "ping" every supported device.
        # If device is found, add it to list
        found_devices = []
        for dev in dev_list:
            status = dev.ping()
            # If 1 -> device connected
            if status == 1:
                found_devices.append(ConConDevice(dev, self._config))
            pass
        return sorted(found_devices, key=lambda device: device.name)

    def get_devices(self):
        """
        :return: :class:`collections.OrderedDict` of devices indexed by the
                    device name.
        """
        temp = OrderedDict([(device.name, device) for device
                            in self.get_device_list()])
        return temp

    def get_device_by_name(self, name):
        """ Retrieves device by device name.

        :param name:  Name of the device.
        :return: :class:`~concon.core.ConConDevice`
        """
        try:
            return self.get_devices()[name]
        except KeyError:
            raise ConConError("Device {0} cannot be found.".format(name))


class ConConDevice(object):
    """ Representation of the configurable device."""

    def __init__(self, usb_device, config):
        self._device = usb_device
        self._config = config

    @property
    def name(self):
        return self._device.name

    def save_settings(self, file_name):
        """ Retrieve settings from a device and saves them into a file

        :param file_name: Path to the file with device configuration.
        """
        cfg_pars = BridgeConfigParser(self._device.vid, self._device.pid,
                                      self._config['usb']['timeout'])
        cfg_pars.write_setting_to_cfg_file(file_name)

    def set_from_file(self, file_name):
        """ Loads settings from a configuration file and downloads them into
            the device.

        :param file_name: Path to the file with device configuration.
        """
        cfg_pars = BridgeConfigParser(self._device.vid, self._device.pid,
                                      self._config['usb']['timeout'])
        cfg_pars.read_setting_from_file(file_name,
                                        ignore_errors=False,
                                        try_fix_errors=True)

        cfg_pars.write_setting_to_device()
