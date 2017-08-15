# -*- coding: utf-8 -*-

"""Console script for concon."""

import click
import pkg_resources
import logging
import logging.config
from .supported_devices import SupportedDevices
from .usb_driver import UsbDriver
from .bridge_config_parser import BridgeConfigParser

# DEFAULT_CONFIG = 'config/config.json'
DEFAULT_CONFIG = 'config/config.yml'
DEFAULT_LOG_CONFIG = 'config/logging_global.cfg'


# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('UCA console')

@click.group()
@click.version_option()
@click.option('--config', default=None,
              help="Application specific configuration file.")
@click.option('-d', '--device', default=None,
              help="Selected device to configure.")
@click.pass_context
def main(ctx, config, device, args=None):
    """Tool for configuration of Devices implementing "Uniprot" communication 
    layer over USB (HID profile).
    """
    ctx.obj = {}
    logging.basicConfig(level=logging.DEBUG)
    # TODO: Config doesn't work...
    # logging.config.fileConfig(
    #     pkg_resources.resource_filename('concon', DEFAULT_LOG_CONFIG)
    # )

    try:
        if config is None:
            config = pkg_resources.resource_filename('concon', DEFAULT_CONFIG)
        devices = SupportedDevices(config)
        usb = UsbDriver.init_from_config(config)
    except OSError as e:
        msg = " Invalid file path or configuration file: {0}!\n".format(str(e))
        logger.error("[SupportedDevices]" + msg)

    dev_list = devices.get_connected_devices()

    # Now try to "ping" every supported device. If device found, add it to list
    found_devices = []
    for dev in dev_list:
        status = dev.ping()
        # If 1 -> device connected
        if status == 1:
            found_devices.append(dev)

    # Test if there is at least one device
    if len(found_devices) == 0:
        msg = "No supported device found! Please make sure, that device is\n" + \
              " properly connected. Also check if device is in supported\n" + \
              " devices list.\n"
        logger.error(msg)
        raise click.Abort()

    found_devices = sorted(found_devices, key=lambda device: device.uid)
    ctx.obj['found_devices'] = found_devices

    if len(found_devices) == 1:
        ctx.obj['device'] = found_devices[0]
    else:
        ctx.obj['device'] = None

    # VID = found_devices[user_choice].vid
    # PID = found_devices[user_choice].pid
    # # End of Else len(found_devices) != 1
    #
    # # Test if there is only one device connected. If not, then user must decide
    # # which want program
    # if (len(found_devices) != 1):
    #     logger.info("Found {0} devices\n".format(len(found_devices)))
    #
    #     # Test if we just want configure first device (useful for quick debug)
    #     if (use_first_dev == 1):
    #         logger.info(
    #             "Parameter use first device set. Following device will be"
    #             "configured:\n{0}\n".format(found_devices[0]))
    #         VID = found_devices[0].vid
    #         PID = found_devices[0].pid
    #     else:
    #         # User must select
    #         print("Please select one device:")


@main.command()
@click.argument("file_name")
def write(file_name):
    """ Write a configuration file to a given device."""
    click.echo("Writing a filename: {0}".format(file_name))


@main.command()
@click.argument("file_name")
@click.pass_context
def read(ctx, file_name):
    """ Read given device configuration and store it in a configuration file."""
    click.echo("Reading to a filename: {0}".format(file_name))
    # Try to initialize bridge
    device = ctx.obj['device']

    cfgPars = BridgeConfigParser(device.vid, device.pid)

    try:
        cfgPars.write_setting_to_cfg_file("test.cfg")
    except Exception as e:
        # If something fails -> try at least close device properly
        cfgPars.close_device()
        raise Exception(e)


@main.command(name="list")
@click.pass_context
def device_list(ctx):
    """ List all available Uniprot devices."""
    found_devices = ctx.obj['found_devices']
    for i in range(len(found_devices)):
        click.echo(" Dev# {0} Name: {1}".format(
            i, found_devices[i].name))

if __name__ == "__main__":
    main()
