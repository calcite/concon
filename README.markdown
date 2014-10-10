# Configuration Console (ConCon)

## Description
 Configuration tool for defices supporting the "Uniprot" protocol over USB (HID profile).
 This tool doesn't need any device-specific driver of ini file, everything is read from
 the device.
 
## Compatible devices
 Devices must fullfill folowing to communicate with ConCon:
 * USB interface with "uniprot" communication layer (data secure)
 * Device must support "generic driver" (common way how to communicate with
   any low level driver) and "HW bridge uniprot" (data from generic driver are
   send through uniprot)
 

## Workflow
 * Download all device options and dynamically create configuration file
 * User modify configuration file
 * Upload configuration back to device 
 
## Files
 * concon.py - Main file.
 * UCA_lib/bridge_config_parser.py - Create and load configuration files 
 * UCA_lib/crc16_xmodem.py - CRC algorythm used by uniprot
 * UCA_lib/driver_usb.py - USB HID driver
 * UCA_lib/usb_driver_lib - Directory with drivers for Linux and Windows
 * UCA_lib/HW_bridge_uniprot.py - Virtual bridge between uniprot and higher
   layer from generic driver
   UCA_lib/uniprot.py - Universal protocol which use driver_usb.py functions
   config/logging_global.conf - Allow set log level for almost every layer
   config/config.json - General configuration (supported Vendor ID's, 
   						Ignored Device ID's)

## Usage
 `python concon.py`
 
## Notes
 * Tested on Linux with python 2.7, 3.2, 3.3 and 3.4
 * Tested on Windows XP and Windows 7 with python 2.7 (but it should work on
   version 3.2, 3.3 and so on)
 * For more info run application with "-h" parameter
