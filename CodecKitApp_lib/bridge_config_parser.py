#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file
# @brief Python script for configuration parser
#
# @author Martin Stejskal

##
# @brief For logging events
import logging
import logging.config


from HW_bridge_uniprot import *

import ConfigParser

## Load configure file for logging
logging.config.fileConfig('config/logging_global.conf', None, False)

##
# @brief Get logging variable
logger = logging.getLogger('Bridge config parser')


# Because in pure ConfigParser there is no option to write comments directly
# http://stackoverflow.com/questions/8533797/adding-comment-with-configparser
class ConfigParserWithComments(ConfigParser.ConfigParser):
    def add_comment(self, section, comment):
        self.set(section, '; ' + comment, None)

    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % ConfigParser.DEFAULTSECT)
            for (key, value) in self._defaults.items():
                self._write_item(fp, key, value)
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for (key, value) in self._sections[section].items():
                self._write_item(fp, key, value)
            fp.write("\n")

    def _write_item(self, fp, key, value):
        if key.startswith(';') and value is None:
            fp.write("%s\n" % (key,))
        else:
            fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))




class BridgeConfigParser():
    # @brief: "Constants"
    # @{
    MAX_RETRY_CNT = 1
    # @}
    bridge = None
    
    
    class SETTING_STRUCT_CHANGE_PARAM(SETTING_STRUCT):
        def __init__(self, setting_struct=None):
            SETTING_STRUCT.__init__(self)
            # If parameter setting_struct exist (is given)
            if (setting_struct):
                # Then just update structure
                self.__dict__.update(setting_struct.__dict__)
            
            # Extra variable
            self.changed = False
        def __str__(self):
            return super(BridgeConfigParser.SETTING_STRUCT_CHANGE_PARAM, self).__str__() +\
            " Changed: {0}\n".format(self.changed)
    
    
    ##
    # @brief Initialize procedure
    def __init__(self):
        self.s_cfg_settings = []
        
        
        # Try initialize Bridge
        retry_cnt = -1
        while(1):
            retry_cnt = retry_cnt +1
            
            if(retry_cnt > BridgeConfigParser.MAX_RETRY_CNT):
                logger.critical("[__init__] Can not initialize Bridge\n")
                raise Exception(" Can not initialize Bridge")
            
            
            try:
                BridgeConfigParser.bridge = Bridge()
            except Exception as e:
                logger.error("[Bridge]" + str(e))
                continue
            else:
                break
        
        logger.info(" All configurations from device downloaded\n")
        
        # Copy whole settings to array s_cfg_settings - go thru all devices
        num_of_dev = BridgeConfigParser.bridge.get_max_Device_ID()
        for DID in range(num_of_dev +1):
            # Copy thru all commands
            # Get max CMD ID for actual device
            max_CMD_ID = BridgeConfigParser.bridge.device_metadata[DID].MAX_CMD_ID
            
            
            temp = []
            for CMD_ID in range(max_CMD_ID+1):
                # Add loaded descriptor, data types and so on
                temp.append(self.SETTING_STRUCT_CHANGE_PARAM(
                    BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID]))
                # Add (set) another extra variable. So far value was not
                # changed
                temp[CMD_ID].changed = False
            
            # And add all CMD ID for actual device to s_cfg_settings
            self.s_cfg_settings.append(temp)
        
        """ Algorithm for print configuration
        """
        for DID in range(num_of_dev+1):
            max_CMD_ID = BridgeConfigParser.bridge.device_metadata[DID].MAX_CMD_ID
            for CMD_ID in range(max_CMD_ID+1):
                logger.debug(str(self.s_cfg_settings[DID][CMD_ID]))
        # """
        
        logger.info(" Actual configuration saved")
    
    
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Write loaded settings from bridge to file
    def write_setting_to_cfg_file(self, filename):
        # Initialize config parser
        config = ConfigParserWithComments()
        
        
        # Get number of devices -> for cycle 1
        num_of_dev = BridgeConfigParser.bridge.get_max_Device_ID()
        
        for DID in range(num_of_dev +1):
            # Show metadata of HW[DID]
            logger.info("[write_setting_to_cfg_file] Device:\n\n" +
                         str(BridgeConfigParser.bridge.device_metadata[DID])
                         + "\n")
            
            # Get max CMD ID for actual device
            max_CMD_ID = BridgeConfigParser.bridge.device_metadata[DID].MAX_CMD_ID
            
            # Add command
            section = BridgeConfigParser.bridge.device_metadata[DID].descriptor
            config.add_section(section)
            comment = "Device ID (DID): " + str(DID)
            config.add_comment(section, comment)
            
            # Go thru all CMD ID
            for CMD_ID in range(max_CMD_ID +1):
                # Write all necessary data
                
                # Create section
                section = BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].descriptor
                config.add_section(section)
                
                
                
                # Test for input and output type is void
                if(
                   (BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type ==
                   BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_type)
                   and
                   (BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type ==
                    BridgeConfigParser.bridge.DATA_TYPES.void_type)
                   ):
                    comment = "Set call_function to non zero if you want call"\
                              " this function"
                    config.add_comment(section, comment)
                    config.set(section, "call_function", "0")
                
                # Else test only for input void (there is non-void output)
                elif(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type ==
                     BridgeConfigParser.bridge.DATA_TYPES.void_type):
                    comment = "OUT TYPE: " +\
                              BridgeConfigParser.bridge.data_type_to_str(
                              BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_type)\
                              + " < " +\
                              str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_min)\
                              + " : " +\
                              str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_max)\
                              + " > | value: " + str(
                                BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_value)
                    config.add_comment(section, comment)
                    comment = "Set call_function to non zero if you want call"\
                              " this function"
                    config.add_comment(section, comment)
                    config.set(section, "call_function", "0")
                
                # Test if just output type is void - again different format and comments 
                elif(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_type ==
                     BridgeConfigParser.bridge.DATA_TYPES.void_type):
                    comment = "IN TYPE: " +\
                        BridgeConfigParser.bridge.data_type_to_str(
                        BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type)\
                        + " < " +\
                        str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_min)\
                        + " : " +\
                        str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_max)\
                        + " >"
                    config.add_comment(section, comment)
                    config.set(section, "value", "not changed")
                    
                    
                
                # Now compare IN TYPE and OUT TYPE and if they have same range
                elif(
                   (BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type ==
                   BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_type)
                   and
                   (BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_min ==
                    BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_min)
                   and
                   (BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_max ==
                    BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_max)
                   ):
                    # If equal - just add comment with data type, min, max and
                    # actual value
                    
                    comment = "TYPE: " +\
                        BridgeConfigParser.bridge.data_type_to_str(
                          BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type)\
                        + " < " +\
                        str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_min)\
                        + " : " +\
                        str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_max)\
                        + " > | origin value: " +\
                        str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_value)
                    config.add_comment(section, comment)
                        
                    config.set(section, "value", str(
                        BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_value))
                    
                # Else just write in and out type, out value
                else:
                    comment = "IN TYPE: " +\
                      BridgeConfigParser.bridge.data_type_to_str(
                      BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_type)\
                      + " < " +\
                      str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_min)\
                      + " : " +\
                      str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].in_max)\
                      + " >"
                    config.add_comment(section, comment)
                    comment = "OUT TYPE: " +\
                      BridgeConfigParser.bridge.data_type_to_str(
                      BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_type)\
                      + " < " +\
                      str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_min)\
                      + " : " +\
                      str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_max)\
                      + " > | out value: " +\
                      str(BridgeConfigParser.bridge.get_all_settings[DID][CMD_ID].out_value)
                    config.add_comment(section, comment)
                    
                    config.set(section, "in_value", "not changed")
        
        
        # Write configuration data to file
        with open(filename, 'wb') as configfile:
            config.write(configfile)
        
        logger.info("[write_setting_to_cfg_file] Data written to file\n")
        
        
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Read setting from file and 
    def read_setting_from_file(self, filename):
        # Initialize config parser
        config = ConfigParser.ConfigParser()
        
        logger.info("[read_setting_from_file] So far nothing")
        
        
        # Read setting by setting and compare if there is change. If yes, then
        # write change flag which will be used for sending new setting
        num_of_dev = BridgeConfigParser.bridge.get_max_Device_ID()
        for DID in range(num_of_dev +1):
            # Get max CMD ID for actual device
            max_CMD_ID = BridgeConfigParser.bridge.device_metadata[DID].MAX_CMD_ID
            
            for CMD_ID in range(max_CMD_ID+1):
                print("TEST")
        print("EOL")
        
        
    def demo_cteni_zapis_cfg(self):
        config.add_section('CDE')
        config.set('CDE', 'DESCRIPTOR', 'Some device with some functions')
        config.set('CDE', 'VAL', '213')
        
        config.add_section('Func1')
        config.set('Func1', 'DESCRIPTOR', 'Hidden Game')
        config.set('Func1', 'VAL dsd', '6543')
        
        
        with open('test.cfg', 'wb') as configfile:
            config.write(configfile)
        
        
        logger.info("Write done\n")
        
        config.read('test.cfg')
        print( config.get('CDE', 'DESCRIPTOR'))
        print( config.get('Func1', 'VAL dsd'))
        
        num = config.getint('Func1', 'VAL dsd')
        num = num + 1
        print( num )
        
        logger.info("Read done\n")