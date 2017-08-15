# -*- coding: utf-8 -*-

from .supported_devices import SupportedDevices
from .usb_driver import usb_ping_device, usb_load_config

import pkg_resources
import logging
import logging.config

DEFAULT_CONFIG = 'config/config.yml'

logger = logging.getLogger(__name__)

class ConCon:
    """ Representation of Configured device."""

    def __init__(self, config=None):
        #
        try:
            if config is None:
                config = pkg_resources.resource_filename('concon', DEFAULT_CONFIG)
            devices = SupportedDevices(config)
            usb_load_config(config)
        except OSError as e:
            msg = " Invalid file path or configuration file: {0}!\n".format(str(e))
            logger.error("[SupportedDevices]" + msg)
        self._config =
        pass

    def _get_device_from_string(self, device_string):
        """ Get device from device name or device number on the list."""
        pass

    def get_device_list(self):
        pass
