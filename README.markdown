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

## Syntax of description fields

Currently the system only generates config files with "windows" ini-like syntax,
(with description fields in comments), but it's planned to support GUI
in the future (most likely in property-grid-like fashion). For that, some 
special syntax can be used to define GUI of each setting.
 * List of options:
	
	{L} val1:option1; val2:option2; val3:option3;...;N:some final note

  Final note is optional.

 * Checkbox:

	{C} option_description

 * Slider:

	{S} option_description; step:value

 * Arrowbox:

	{A} option_description; step:value

 * Eval expansion - this option is to save the length of strings which needs
to be stored in the MCU's code for descriptors. Instead, one can write a Python 
expression which will be expanded to a string and processed.
  Example:

	{L}0:fsref/1; 1:fsref/1.5; 2:fsref/2; 3:fsref/2.5; 4:fsref/3; 
	5:fsref/3.5; 6:fsref/4; 7:fsref/4.5; 8:fsref/5; 9:fsref/5.5; 10:fsref/6

  This is may be way too long for MCU with limited code memory. Easier to use 
eval expansion (start line with '='):
 
	='{L}'+'; '.join(['{0}:fsref/{1}'.format(i,i*0.5+1) for i in range(0,11)])

  which will be expanded to the same thing.

 
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
