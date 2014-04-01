# Universal Control Application

## Description
 Application allow easily configure device wihtout extra knowledge about it.
 Application can work with devices which comply these conditions:
 * USB interface with "uniprot" communication layer (data secure)
 * Device must support "generic driver" (common way how to communicate with
   any low level driver) and "HW bridge uniprot" (data from generic driver are
   send through uniprot)
 

## Workflow
 * Download all device options and dynamicly create configuration file
 * User modify configuration file
 * Upload configuration back to device 
 
## Files
 * UniversalControlApp_console.py - Main file.
 * UCA_lib/bridge_config_parser.py - Create and load configuration files 
 * UCA_lib/crc16_xmodem.py - CRC algorythm used by uniprot
 * UCA_lib/driver_usb.py - USB HID driver
 * UCA_lib/HW_bridge_uniprot.py - Virtual bridge between uniprot and higher
   layer from generic driver
   UCA_lib/uniprot.py - Universal protocol which use driver_usb.py functions
   config/logging_global.conf - Allow set log level for almost every layer

## Usage
 `python UniversalControlApp_console.py`

## Get source code!
 `git clone http://10.54.13.215/gitlab/martin.stej/codeckit-controlapp.git`
 
## Notes
 * Tested on Python 2.7
 * Application is so far tested on Windows7
 * For more info run application with -h parameter