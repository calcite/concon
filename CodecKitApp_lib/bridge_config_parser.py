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

import re

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
            
            # Extra variables
            
            # Just for checking if variable was changed in cfg file
            self.changed = False
            # In some cases is useful when CMD_ID is also stored in memory
            self.CMD_ID = -1
        
        
        def __str__(self):
            return super(BridgeConfigParser.SETTING_STRUCT_CHANGE_PARAM, self).__str__() +\
            " Changed: {0}\n CMD ID: {1}\n".format(self.changed,self.CMD_ID)
            
        def export_to_config(self, config):
            
            # Create section
            section = self.name
            config.add_section(section)
            
            # If there is some descriptor -> add it!
            if(self.descriptor != ""):
                comment = self.descriptor
                config.add_comment(section, comment)
            
            # Test for input and output type is void
            if(
                (self.in_type == self.out_type)
                and
                (self.in_type == BridgeConfigParser.bridge.DATA_TYPES.void_type)
                ):
                comment = "Set call_function to non zero if you want call"\
                          " this function"
                config.add_comment(section, comment)
                config.set(section, "call_function", "0")
                
            # Else test only for input void (there is non-void output)
            elif(self.in_type ==
                BridgeConfigParser.bridge.DATA_TYPES.void_type):
                comment = "OUT TYPE: {0} < {1} : {2} > | value: {3}".format(
                          BridgeConfigParser.bridge.data_type_to_str(self.out_type),
                          self.out_min,
                          self.out_max,
                          self.out_value)
                config.add_comment(section, comment)
                comment = "Set call_function to non zero if you want call"\
                          " this function"
                config.add_comment(section, comment)
                config.set(section, "call_function", "0")
            
            # Test if just output type is void - again different format and comments 
            elif(self.out_type ==
                             BridgeConfigParser.bridge.DATA_TYPES.void_type):
                comment = "IN TYPE: " +\
                        BridgeConfigParser.bridge.data_type_to_str(
                        self.in_type)\
                        + " < " +\
                        str(self.in_min)\
                        + " : " +\
                        str(self.in_max)\
                        + " >"
                config.add_comment(section, comment)
                config.set(section, "value", "not changed")
                    
                    
                
            # Now compare IN TYPE and OUT TYPE and if they have same range
            elif(
                (self.in_type ==
                self.out_type)
                and
                (self.in_min ==
                self.out_min)
                and
                (self.in_max ==
                self.out_max)
                ):
                # If equal - just add comment with data type, min, max and
                # actual value
                
                comment = "TYPE: " +\
                    BridgeConfigParser.bridge.data_type_to_str(
                    self.in_type)\
                    + " < " +\
                    str(self.in_min)\
                    + " : " +\
                    str(self.in_max)\
                    + " > | current value: " +\
                    str(self.out_value)
                config.add_comment(section, comment)
                        
                config.set(section, "value", str(self.out_value))
                
            # Else just write in and out type, out value
            else:
                comment = "IN TYPE: " +\
                  BridgeConfigParser.bridge.data_type_to_str(
                  self.in_type)\
                  + " < " +\
                  str(self.in_min)\
                  + " : " +\
                  str(self.in_max)\
                  + " >"
                config.add_comment(section, comment)
                comment = "OUT TYPE: " +\
                  BridgeConfigParser.bridge.data_type_to_str(
                  self.out_type)\
                  + " < " +\
                  str(self.out_min)\
                  + " : " +\
                  str(self.out_max)\
                  + " > | out value: " +\
                  str(self.out_value)
                config.add_comment(section, comment)
                
                config.set(section, "in_value", "not changed")
            
    class GroupParam(SETTING_STRUCT_CHANGE_PARAM):
        
        def __init__(self,setting_struct=None):
            BridgeConfigParser.SETTING_STRUCT_CHANGE_PARAM.__init__(self, setting_struct)
            self._choice_params = []

  
        def add_choice_param(self, param):
            self._choice_params.append(param)
            
        def export_to_config(self, config):
             # Create section
            section = self.name
            config.add_section(section)
            config.add_comment(section,
              "TYPE: {0} < {1} : {2} > | current value: {3} |"\
              " Available choices:".format(
                        BridgeConfigParser.bridge.data_type_to_str(self.out_type),
                        self.out_min,
                        self.out_max,
                        self.out_value))
            for choice_param in self._choice_params:
                # Test if data type is void or not
                if(choice_param.out_type ==
                   BridgeConfigParser.bridge.DATA_TYPES.void_type):
                    
                    # Test if descriptor is empty. If yes, then show at
                    # least name
                    if(choice_param.descriptor == ""):
                        config.add_comment(section, "{id}: {description}".format(
                          description=choice_param.name,
                          id = choice_param.CMD_ID))
                    else:
                        config.add_comment(section, "{id}: {description}".format(
                          description=choice_param.descriptor,
                          id = choice_param.CMD_ID))
                else:
                    # Test if descriptor is empty. If yes, then show at
                    # least name
                    if(choice_param.descriptor == ""):
                        config.add_comment(section,
                          "{id}: {description} | return: {val}".format(
                          description=choice_param.name,
                          id=choice_param.CMD_ID,
                          val=choice_param.out_value))
                    else:
                        config.add_comment(section,
                          "{id}: {description} | return: {val}".format(
                          description=choice_param.descriptor,
                          id=choice_param.CMD_ID,
                          val=choice_param.out_value))
            # out value
            config.set(section, "selected_value", str(self.out_value))
    
    
    
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
            
            # Temporary array for settings
            temp = []
            
            # Dictionary for groups (CMD_ID and "group name")
            groups = {}
            
            cnt = 0
            # Go thru all CMD_ID
            for setting in BridgeConfigParser.bridge.get_all_settings[DID]:
                
                # Test if group header found
                if (setting.in_type == \
                        BridgeConfigParser.bridge.DATA_TYPES.group_type):
                    # Create key in dictionary (will be filled later)
                    tmpst = self.GroupParam(setting)
                    groups[tmpst.name] = tmpst
                    logger.debug(" Found group header: {0}\n".format(setting))
                else:
                    tmpst = self.SETTING_STRUCT_CHANGE_PARAM(setting)
                    
                # Anyway: always set changed variable to false (so far
                # nothing was changed)
                tmpst.changed = False
                
                tmpst.CMD_ID = cnt
                
                # Add to temp array
                temp.append(tmpst)
                
                cnt = cnt +1
            
            
            items_to_remove = []
            for setting in temp:
                # Compare with group pattern
                match_result = re.match("{([a-zA-Z0-9_ ]+)}",
                                        setting.name)
                
                # If match -> add actual setting move to groups
                if (match_result):
                    logger.debug(" Found group item:" + str(setting) + "\n")
                    
                    # Add group to dictionary
                    groups[match_result.group(1)].add_choice_param(setting)
                    items_to_remove.append(setting)
                    
            #Remove duplicated items (this cannot be done in the for cycle above)
            for item in items_to_remove:
                temp.remove(item)
                    
            
            # And add all CMD ID for actual device to s_cfg_settings
            self.s_cfg_settings.append(temp)
        
        
        
        logger.info(" Actual configuration saved")
    
    
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Write loaded settings from bridge to file
    def write_setting_to_cfg_file(self, filename):
        # Initialize config parser
        config = ConfigParserWithComments()
        
        
        num_of_dev = BridgeConfigParser.bridge.get_max_Device_ID()
        
        for DID in range(num_of_dev +1):
            section = BridgeConfigParser.bridge.device_metadata[DID].descriptor
            config.add_section(section)
            config.add_comment(section,"Device ID (DID): " + str(DID))
            
            # Go thru command by command in device (DID)
            for setting in self.s_cfg_settings[DID]:
                setting.export_to_config(config)
        
        
        
        
        
        
        
        
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