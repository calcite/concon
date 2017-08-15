#!/usr/bin/env python
# -*- coding: utf-8 -*-

# USB driver for Linux. Use pyusb library
#
# Author: Martin Stejskal

import usb.core
import usb.util


class HidDeviceStruct(object):
    """
    Structure which contains all necessary HID profile data
    """

    def __init__(self):
        self.device = -1  # When closing we need device object. Else is enough
        # interface and EP. So to make process simple we store
        # device object and interface and EP objects
        self.interface = -1
        self.ep_in = -1
        self.ep_out = -1

    def __str__(self):
        return "Interface number: {0}\n" \
               "EP IN address: {1}\n" \
               "EP OUT address: {2}\n" \
            .format(self.interface,
                    self.ep_in.bEndpointAddress,
                    self.ep_out.bEndpointAddress)


def usb_lib_ping_device(vid, pid):
    """
    Just test if selected device is connected

    :param vid: VendorID
    :type vid: 16 bit number
    :param pid: ProductID
    :type pid: 16 bit number
    """
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if dev is None:
        return 404  # Device not found
    else:
        return 1  # Device found


def usb_lib_open_device(vid, pid):
    """
    Open USB device. Should be called as first

    :param vid: VendorID
    :type vid: 16 bit number
    :param pid: ProductID
    :type pid: 16 bit number
    """

    # Flags which indicate if IN/OUT EP was found
    found_in_ep = 0
    found_out_ep = 0

    dev_hid = HidDeviceStruct()

    # Test if device exist
    dev = usb.core.find(idVendor=vid, idProduct=pid)
    if dev is None:
        return 404  # Device not found
    else:
        # Device found -> test if device have HID profile and if yes, then
        # detach kernel driver

        # Go through all configurations
        for cfg in dev:
            # Go through all interfaces
            for interface in cfg:
                # Test interface class and subclass
                # (generic (0) HID (3) profile)
                if ((interface.bInterfaceClass == 3) and
                        (interface.bInterfaceSubClass == 0)):
                    # Our device found! So now try to found IN and OUT EP
                    for ep in interface:
                        # Test EP for necessary configuration
                        if ((ep.bLength == 7) and
                                (ep.bmAttributes == 3) and
                                (ep.wMaxPacketSize == 8)):

                            # Correct configuration.
                            # Test EP direction (if>=128 -> IN)
                            if ep.bEndpointAddress >= 128:
                                # EP found -> set flag.
                                # Also save endpoint object
                                found_in_ep = 1
                                dev_hid.ep_in = ep
                            else:
                                found_out_ep = 1
                                dev_hid.ep_out = ep

                    # When here all EP was checked.
                    # So check if EP IN and EP OUT are accessible
                    if (found_in_ep == 1) and (found_out_ep == 1):
                        # All OK -> save device, interface and break
                        dev_hid.device = dev
                        dev_hid.interface = interface.bInterfaceNumber
                        break

            if (found_in_ep == 1) and (found_out_ep == 1):
                # All OK -> break
                break

        # If all OK -> return device interface with generic HID
        if (found_in_ep == 1) and (found_out_ep == 1):

            # Test if driver is attached to kernel.
            # If not, try to attach it back
            if not dev.is_kernel_driver_active(dev_hid.interface):
                raise Exception(
                    "It looks like some process uses HID interface."
                    " Or maybe some \n"
                    "program that used HID interface crash"
                    " or forget close device.\n"
                    "So please make sure that device is not using another\n"
                    "program and then reconnect device. "
                    "Sorry for troubles, but\n"
                    "this is the only solution for now :(")
            # Detach kernel driver -> device under control (R/W)
            dev.detach_kernel_driver(dev_hid.interface)
            return dev_hid

    # Else there is something wrong -> return 404 -> not found
    return 404


def usb_lib_close_device(device):
    """
    Close USB device. Should be called as last
    :param device: device object
    """
    # Attach device back to kernel
    usb.util.dispose_resources(device.device)
    device.device.attach_kernel_driver(device.interface)

    return 0


def usb_lib_tx_data(device, data_8bit, timeout):
    """
    Send data (64 bits per 8 bits) over USB interface

    :param device: device description, witch programmer get when use function
     usb_open_device
    :param data_8bit: Data to TX (8 bytes -> 64 bits)
    :type data_8bit: List of 8 bit data values
    :param timeout:
    """
    try:
        device.ep_out.write(data_8bit, timeout)
    except:
        print("\n--------------------\nTX Timeout!\n---------------------\n")
        return -1

    return 0


def usb_lib_rx_data(device, timeout):
    """
    Receive data from USB interface (8x8bits)

    :param device: Device description, witch programmer get when use function
     usb_open_device
    :param timeout:
    """

    # Read 8 bytes
    try:
        in_data = device.ep_in.read(8, timeout)
    except:
        # Timeout -> load dummy data
        print("\n--------------------\nRX Timeout!\n---------------------\n")
        in_data = [0xFF0] * 8
        return in_data

    return in_data
    # TODO - cleanup - this below doesn't make sense
    ret_data = [0x00] * 8

    print(in_data)
    for i in range(8):
        ret_data[i] = in_data[i]
    print(ret_data)
    print("-------------------------\n")

    return ret_data


def usb_list_connected_devices(vid=None):
    """
    List all connected devices, optionally filter only devices with given
    Vendor ID.

    :param vid:     (Optional) Vendor ID.

    :return: List of (name, vid, pid, uid) tuples.
    """
    kwargs = {'find_all': True, 'idVendor': vid, } if vid else \
        {'find_all': True, }
    devices = []

    for device in usb.core.find(**kwargs):
        name = device.product or device.address
        uid = device.bus * 0xff + device.address
        devices.append((name, device.idVendor, device.idProduct, uid))
    return devices
