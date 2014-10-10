#!/usr/local/bin/python
# encoding: utf-8
'''
Configuration Console for command line.

Tool for configuration of Devices implementing "Uniprot" communication layer over USB (HID profile).

@author:     Martin Stejskal

@copyright:  2014 ALPS Electric Ltd,. All rights reserved.

@license:    license

@contact:    martin.stej@gmail.com
@deffield    updated: 10.10.2014 by Josef Nevrly
'''

import sys
sys.path.append("UCA_lib")

# Allow create and load device depend configuration file
from UCA_lib.bridge_config_parser import *

# Get list of supported devices from configuration file
from UCA_lib.supported_devices import *

# Allow "ping" devices
from UCA_lib.usb_driver import usb_ping_device

# Time operations
from time import sleep

# For processing arguments
import sys
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.7
__date__ = '2014-03-31'
__updated__ = '2014-10-10'

DEBUG = 0


##
# Libraries for log events
import logging
import logging.config

logger = logging.getLogger('UCA console')



class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg



def main(argv=None):
  """
  Main console function
  :param argv: Arguments
  """
  if argv is None:
    argv = sys.argv
  else:
    sys.argv.extend(argv)

  program_name = os.path.basename(sys.argv[0])
  program_version = "v%s" % __version__
  program_build_date = str(__updated__)
  program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
  program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
  program_license = '''%s

  Tool for configuration of Devices implementing "Uniprot" communication layer over USB (HID profile).
  
  Created by Martin Stejskal on %s.
  Copyright 2014 ALPS. All rights reserved.
  
USAGE

    To read configuration from device to a specific file:
        concon.py -r -d specific_file.cfg
    
    To upload configuration file into a device
        concon.py -w -d specific_file.cfg
''' % (program_shortdesc, str(__date__))



  # Default values
  LOGGING_CONFIG_FILE = "config/logging_global.cfg"
  DEVICE_CONFIG_FILE = "device.cfg"
  rw_mode = "r"
  verbose_lvl = 0
  use_first_dev = 0
  CONFIG = "config/config.json"



  # Try to process arguments
  try:
    # Setup argument parser
    parser = ArgumentParser(description=program_license,
                            formatter_class=RawDescriptionHelpFormatter)
    # Read and write can not be set on one time
    group = parser.add_mutually_exclusive_group()
    group.add_argument( "-r",
                        "--read",
                        dest="read_cfg",
                        action="store_true",
                        help="read device configuration to file [default"
                             " parameter: %(default)s]"
                             "[default configuration file: device.cfg]",
                        default=rw_mode,)
    group.add_argument( "-w",
                        "--write",
                        dest="write_cfg",
                        action="store_true",
                        help="write configuration to device [default"
                        " parameter: %(default)s]"
                        "[default configuration file: device.cfg]",
                        default=rw_mode)
    parser.add_argument("-d",
                        "--device",
                        dest="device_cfg_path",
                        help="path to device configuration file "
                        "[default: %(default)s]",
                        default=DEVICE_CONFIG_FILE)
    parser.add_argument("-C",
                        "--config",
                        dest="config_path",
                        help="path to configuration file "
                        "[default: %(default)s]",
                        default=CONFIG)
    parser.add_argument("-l",
                        "--log",
                        dest="log_cfg_path",
                        help="Path to log configuration file "
                        "[default: %(default)s]",
                        default=LOGGING_CONFIG_FILE)
    parser.add_argument("-f",
                        "--first",
                        dest="use_first_dev",
                        type=int,
                        help="{0,1}"
                        " When more than one device found and this option "
                        "is set, then configure just first device found in "
                        "supported device list. Else ask user which device "
                        "want configure "
                        "[default: %(default)s]",
                        default=use_first_dev)
    parser.add_argument('-V',
                        '--version',
                        action='version',
                        version=program_version_message)
    parser.add_argument("-v",
                        "--verbose",
                        dest="verbose",
                        action="count",
                        help="enable verbose mode [default: %(default)s]",
                        default=verbose_lvl)

    # Process arguments
    args = parser.parse_args()

    # If not empty, then overwrite origin value
    if( args.log_cfg_path != None ):
      LOGGING_CONFIG_FILE = args.log_cfg_path

    if( args.device_cfg_path != None ):
      DEVICE_CONFIG_FILE = args.device_cfg_path

    if( args.config_path != None):
      config_file = args.config_path
    # Save verbose level
    if( args.verbose > 0):
      verbose_lvl = args.verbose

    if( args.read_cfg == True):
      rw_mode = "r"
    if( args.write_cfg == True):
      rw_mode = "w"



    if( args.use_first_dev != None):
      use_first_dev = args.use_first_dev

  except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
  except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2






  # All arguments are now processed

  ## Load configure file for logging
  logging.config.fileConfig(LOGGING_CONFIG_FILE, None, False)
  logger.info("v{0} Alive!\n".format(__version__))

  # Check use_first_dev value
  if((use_first_dev != 0) and (use_first_dev != 1)):
    logger.warning("Parameter use first device have invalid value.\nParameter"
                   "will be set to 0\n(use first device feature will be"
                   " disabled\n")
    use_first_dev = 0

  # Write info about actual configuration only if verbose is enabled
  if(verbose_lvl > 0):
    # R/W mode
    logger.info("Read/write mode: {0}\n"
                "Device configuration file: {1}\n"
                "File with supported devices: {2}\n"
                "Log configuration file: {3}\n"
                "Verbose level: {4}\n".format(rw_mode,
                                              DEVICE_CONFIG_FILE,
                                              config_file,
                                              LOGGING_CONFIG_FILE,
                                              verbose_lvl))
  else:
    # Write just info about configuration file
    if(rw_mode == "r"):
      logger.info("Configuration file for device will be created\n")
    else:
      logger.info("Configuration data will be written to device\n")



  # Try get list of known devices
  try:
    devices = SupportedDevices(config_file)
    dev_list = devices.get_connected_devices()
  except Exception as e:
    msg = " Invalid file path or configuration file: {0}!\n".format(str(e))
    logger.error("[SupportedDevices]" + msg)
    raise Exception(msg)

  # If verbose show supported devices
  if(verbose_lvl >1):
    msg = ""
    for dev  in dev_list:
      msg = msg + str(dev)
    logger.info("Supported devices:\n{0}\n".format(msg))

  # Now try to "ping" every supported device. If device found, add it to list
  found_devices = []
  for dev in dev_list:
    status = usb_ping_device(dev.vid, dev.pid)
    # If 1 -> device connected
    if(status == 1):
      found_devices.append(dev)

  # Test if there is at least one device
  if(len(found_devices) == 0):
    msg = "No supported device found! Please make sure, that device is\n" +\
          " properly connected. Also check if device is in supported\n"+\
          " devices list.\n"
    logger.error("[Number of devices]" + msg)
    raise Exception(msg)


  # Test if there is only one device connected. If not, then user must decide
  # which want program
  if(len(found_devices) != 1):
    logger.info("Found {0} devices\n".format(len(found_devices)))

    # Test if we just want configure first device (useful for quick debug)
    if(use_first_dev == 1):
      logger.info("Parameter use first device set. Following device will be"
                  "configured:\n{0}\n".format(found_devices[0]))
      VID = found_devices[0].vid
      PID = found_devices[0].pid
    else:
      # User must select
      print("Please select one device:")

      while(1):
        for i in range(len(found_devices)):
          print(" Device number [{0}] Name: {1}".format(i, found_devices[i].name))
        print("<----------------------------------------------->")
        if(sys.version_info[0] == 2):
          user_choice = raw_input("Selected device number: ")
        elif(sys.version_info[0] == 3):
          user_choice = input("Select device number: ")
        else:
          raise Exception("Unknown python version")
        # Check input
        try:
          user_choice = int(user_choice)
        except:
          print("Please type device number. Try it again ;-)\n")
          continue  # Jump back to begin of while
        # Else conversion to number was success, so check it
        if(user_choice < 0):
          print("Selected option can not be negative. Just type device number.\n"
                "Try it again ;-)")
          continue
        if(user_choice > len(found_devices)):
          print("How can I select device which is not found? So please type\n"
                "correct device number.")
          continue
        # Else user pick correct device
        break
      # End of while
      VID = found_devices[user_choice].vid
      PID = found_devices[user_choice].pid
    # End of Else len(found_devices) != 1
  else:
    # There is just one found device. So inform user which device was selected
    logger.info("Found device:\n   > {0}\n".format(found_devices[0].name))
    VID = found_devices[0].vid
    PID = found_devices[0].pid


  # Try to initialize bridge
  cfgPars = BridgeConfigParser(VID, PID)

  if(rw_mode == "r"):
    # Create config file
    try:
      cfgPars.write_setting_to_cfg_file(DEVICE_CONFIG_FILE)
    except Exception as e:
      # If something fails -> try at least close device properly
      cfgPars.close_device()
      raise Exception(e)
  else:
    # Or read from config file
    try:
      cfgPars.read_setting_from_file(DEVICE_CONFIG_FILE,
                                     ignore_errors=False,
                                     try_fix_errors=True)
      # And send changes to device
      cfgPars.write_setting_to_device()
    except Exception as e:
      # If something fails -> try at least close device properly
      cfgPars.close_device()
      raise Exception(e)





  # Close device properly
  cfgPars.close_device()


  print("\nBye")









if __name__ == "__main__":
  if DEBUG:
    sys.argv.append("-h")
    sys.argv.append("-v")


  sys.exit(main())










