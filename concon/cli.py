#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for concon."""

import click
import pkg_resources
import logging
import logging.config
import yaml
from .supported_devices import SupportedDevices
from .usb_driver import UsbDriver
from .bridge_config_parser import BridgeConfigParser
from .core import ConConError

# DEFAULT_CONFIG = 'config/config.json'
DEFAULT_CONFIG = 'config/config.yml'
DEFAULT_LOG_CONFIG = 'config/logging_global.cfg'

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('UCA console')
logging.config.fileConfig(
    pkg_resources.resource_filename('concon',
                                    DEFAULT_LOG_CONFIG),
    None,
    False)


def report_errors(err):
    click.secho("\n <-------------------- Errors --------------------->",
                fg='red')
    click.echo(err, err=True)


@click.group()
@click.version_option()
@click.option('--config', default=None,
              help="Application specific configuration file.")
@click.option('-d', '--device', default=None,
              help="Selected device to configure.")
@click.pass_context
def main(ctx, config, device, args=None):
    """Tool for configuration of devices implementing "Uniprot" communication
    layer over USB (HID profile).
    """
    ctx.obj = {}
    logging.basicConfig(level=logging.ERROR)
    # TODO: Config doesn't work...
    # logging.config.fileConfig(
    #     pkg_resources.resource_filename('concon', DEFAULT_LOG_CONFIG)
    # )

    try:
        # TODO: Add cascaded configuration
        if config is None:
            config = pkg_resources.resource_filename('concon', DEFAULT_CONFIG)

        with open(config, 'r') as cf:
            conf = yaml.load(cf)
    except OSError as e:
        msg = " Invalid file path or configuration file: {0}!\n".format(str(e))
        report_errors(msg)
        raise click.Abort()

    devices = SupportedDevices(**conf['devices'])
    usb = UsbDriver(timeout=conf['usb']['timeout'])
    ctx.obj['config'] = conf
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
        click.secho(msg, fg='yellow')
        exit()

    found_devices = sorted(found_devices, key=lambda device: device.name)
    ctx.obj['found_devices'] = found_devices

    if len(found_devices) == 1:
        ctx.obj['device'] = found_devices[0]
    else:
        if device is None:
            # Show device selection prompt
            click.secho("More than one configurable devices detected.\n"
                        "Choose one from below and run concon with"
                        " -d [0 ~ {0}] option.".format(len(found_devices) - 1),
                        fg='yellow')
            ctx.invoke(device_list)
            raise click.Abort()

        try:
            ctx.obj['device'] = found_devices[int(device)]
        except (IndexError, ValueError):
            report_errors('Invalid device number "{0}". '
                          'Choose between 0~{1}'.format(device,
                                                        len(found_devices) - 1))
            ctx.invoke(device_list)
            raise click.Abort()


@main.command()
@click.argument("file_name")
@click.pass_context
def write(ctx, file_name):
    """ Write a configuration file to a given device."""

    device = ctx.obj['device']
    label = "Connecting to {0}".format(device.name)
    # Try to initialize bridge
    cfg_pars = None
    try:
        with click.progressbar(length=10, show_eta=False, label=label) as bar:
            cfg_pars = BridgeConfigParser(device.vid, device.pid,
                                          ctx.obj['config']['usb']['timeout'],
                                          progress_bar=bar)

        click.echo("Reading configuration from: {0}".format(file_name))
        cfg_pars.read_setting_from_file(file_name,
                                        ignore_errors=False,
                                        try_fix_errors=False)

        # And send changes to device
        label = "Writing configuration to {0}".format(device.name)
        with click.progressbar(length=10, show_eta=False, label=label) as bar:
            cfg_pars.write_setting_to_device(progress_bar=bar)

        click.secho("Configuration successfully downloaded "
                    "to the device {0}".format(device.name), fg='green')
    except ConConError as ce:
        report_errors(ce)
    finally:
        # If something fails -> try at least close device properly
        if cfg_pars:
            cfg_pars.close_device()


@main.command()
@click.argument("file_name")
@click.pass_context
def read(ctx, file_name):
    """ Read given device configuration and store it in a configuration file."""

    device = ctx.obj['device']
    label = "Reading configuration from {0}".format(device.name)

    # Try to initialize bridge
    cfg_pars = None
    try:
        with click.progressbar(length=10, show_eta=False, label=label) as bar:
            cfg_pars = BridgeConfigParser(device.vid, device.pid,
                                          ctx.obj['config']['usb']['timeout'],
                                          progress_bar=bar)

        cfg_pars.write_setting_to_cfg_file(file_name)
        click.secho("Device configuration written to file {0}".format(
            file_name), fg='green')
    except ConConError as ce:
        report_errors(ce)
    finally:
        if cfg_pars:
            cfg_pars.close_device()


@main.command(name="list")
@click.pass_context
def device_list(ctx):
    """ List all available Uniprot devices."""
    found_devices = ctx.obj['found_devices']
    for i in range(len(found_devices)):
        click.echo(" Dev# {0} <{1}>".format(
            i, found_devices[i].name))

if __name__ == "__main__":
    main()
