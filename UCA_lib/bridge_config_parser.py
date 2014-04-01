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
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
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
            return super(SETTING_STRUCT_CHANGE_PARAM, self).__str__() +\
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
                            BridgeConfigParser.bridge.data_type_to_str(
                                                            self.out_type),
                            self.out_min,
                            self.out_max,
                            self.out_value)
                config.add_comment(section, comment)
                comment = "Set call_function to non zero if you want call"\
                          " this function"
                config.add_comment(section, comment)
                config.set(section, "call_function", "0")
            
            # Test if just output type is void - again different format and
            # comments 
            elif(self.out_type ==
                             BridgeConfigParser.bridge.DATA_TYPES.void_type):
                comment = "IN TYPE: {0} < {1} : {2} >".format(
                            BridgeConfigParser.bridge.data_type_to_str(
                                                            self.in_type),
                            self.in_min,
                            self.in_max)
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
                
                comment = "TYPE: {0} < {1} : {2} > | current value: {3}".format(
                            BridgeConfigParser.bridge.data_type_to_str(
                                                              self.in_type),
                            self.in_min,
                            self.in_max,
                            self.out_value)
                
                config.add_comment(section, comment)
                        
                config.set(section, "value", str(self.out_value))
                
            # Else just write in and out type, out value
            else:
                comment = "IN TYPE: {0} < {1} : {2} >".format(
                            BridgeConfigParser.bridge.data_type_to_str(
                                                              self.in_type),
                            self.in_min,
                            self.in_max)
                config.add_comment(section, comment)
                comment = "OUT TYPE: {0} < {1} : {2} > | out value: {3}".format(
                            BridgeConfigParser.bridge.data_type_to_str(
                                                              self.out_type),
                            self.out_min,
                            self.out_max,
                            self.out_value)
                config.add_comment(section, comment)
                
                config.set(section, "in_value", "not changed")
        
        def import_from_config(self, config,
                               ignore_errors=False,
                               try_fix_errors=False):
            # Check for error input types
            if(self.in_type == BridgeConfigParser.bridge.DATA_TYPES.group_type):
                msg = " Invalid data type: group. Internal error\n"
                logger.error("[import_from_config]" + msg)
                raise Exception(msg)
            
            
            # Find section
            section = self.name
            
            # According to actual input and output data types choose correct
            # variable name
            
            # Test if input type is void
            if(self.in_type == BridgeConfigParser.bridge.DATA_TYPES.void_type):
                # Input and output types are void -> check if function should
                # be called
                value = config.get(section, "call_function")
                if(value != "0"):
                    # Function should be called -> value changed
                    self.out_value = "Call function"
                    
                    self.changed = True
                    
                # Nothing to do here -> return
                return
            
            # Test if just output type is void - again different format and comments 
            elif(self.out_type==BridgeConfigParser.bridge.DATA_TYPES.void_type):
                # Output is void, so we can not know what value was last.
                # However if there were some change, then "value" should be
                # different than "not changed"
                
                # Load value
                value = config.get(section, "value")
                
                # Check if value was not changed
                if(value == "not changed"):
                    return
                
            # Test for same data types and values
            elif((self.out_type == self.in_type) and
                  (self.in_min == self.out_min)  and
                  (self.in_max == self.out_max)
                 ):
                
                value = config.get(section, "value")
                # Check if value is different according to data type
                
                # check if value is number or string/char
                try:
                    value = float(value)
                except:
                    # If fail -> string -> check data IN TYPE with char (only
                    # correct option). If not char -> user fail -> error
                    if(self.in_type != 
                       BridgeConfigParser.bridge.DATA_TYPES.char_type):
                        msg = " Incorrect user value <{0}> at option <{1}>"\
                              " Expected type {2}\n".format(
                                    value,
                                    self.name,
                                    Bridge.data_type_to_str(self.in_type))
                        logger.error("[import_from_config]" + msg)
                        if(ignore_errors == False):
                          raise Exception(msg)
                        return
                    # Else value is character -> change it!
                    else:
                        
                        # Test if there is more characters -> if yes, then
                        # log problem and if needed raise exception
                        if(ignore_errors != False):
                          # Just inform user that there is problem
                            msg = " In option <{0}> expected only one "\
                                  "character, but found string. Using only "\
                                  "first character <{1}>".format(self.name,
                                                                 value[0])
                            logger.warn(msg)
                        else:
                          # Well, else we can not let problem as it as.
                          # Throw exception and log problem
                          msg = " In option <{0}> expected only one "\
                                "character, but found string!".format(
                                                                    self.name)
                          logger.error("[import_from_config]" + msg)
                          raise Exception(msg)
                        
                        
                        # Copy just first character
                        self.out_value = value[0]
                        
                        # Value was changed
                        self.changed = True
                        
                        return
                # Check if value and original value is same
                if(self.out_value == value):
                    # If they are same -> nothing to do -> return
                    return
                
            # Last option: different data types are same
            else:
                value = config.get(section, "in_value")
                
                # Check if value was changed
                if(value == "not changed"):
                    return
            
            
            # Almost done...
            
            try:
                value = float(value)
            except:
                # When fail -> value is string
                # Check for char type -> else there is problem
                if(self.in_type != 
                   BridgeConfigParser.bridge.DATA_TYPES.char_type):
                    msg = " Incorrect user value <{0}> at option <{1}>. "\
                          "Expected type: {2}\n".format(
                                        value,
                                        self.name,
                                        Bridge.data_type_to_str(self.in_type))
                    logger.error("[import_from_config]" + msg)
                    # This problem can not be fixed. But we can ignore this
                    # error, or raise exception
                    if(ignore_errors == False):
                      raise Exception(msg)
                    # Else no exception -> just return
                    else:
                      return
            
            # Retype (if needed) value according to input type
            if((self.in_type != BridgeConfigParser.bridge.DATA_TYPES.float_type)
               and
               (self.in_type != BridgeConfigParser.bridge.DATA_TYPES.char_type)
               ):
                value = int(value)
            
            # Check boundaries
            if(value < self.in_min):
              msg = " At option <{0}> is lower value than"\
                    " expected!\n Expected at least {1} but got {2}.\n".format(
                                                          self.name,
                                                          self.in_min,
                                                          value)
              # Check if we can fix errors
              if(try_fix_errors != False):
                # Can fix -> use minimum -> expand message
                msg = msg + " Value {0} will be used instead.\n".format(
                                                                  self.in_min)
                logger.warn("[import_from_config]" + msg)
                value = self.in_min
              else:
                # Can not fix -> raise exception or just throw this setting
                logger.error("[import_from_config]" + msg)
                if(ignore_errors == False):
                  # No error allowed -> Throw exception
                  raise Exception(msg)
                return
            
            if(value > self.in_max):
              msg = " At option <{0}> is higher value than"\
                    " expected!\n Expected at most {1} but got {2}.\n".format(
                                                          self.name,
                                                          self.in_max,
                                                          value)
              # Check if we can fix errors
              if(try_fix_errors != False):
                # Can fix -> use minimum -> expand message
                msg = msg + " Value {0} will be used instead.\n".format(
                                                                  self.in_max)
                logger.warn("[import_from_config]" + msg)
                value = self.in_max
              else:
                # Can not fix -> raise exception or just throw this setting
                logger.error("[import_from_config]" + msg)
                if(ignore_errors == False):
                  # No error allowed -> Throw exception
                  raise Exception(msg)
                return
            
            
            # Write value
            self.out_value = value
            # Value changed
            self.changed = True
            
            return
            
            
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
class GroupParam(SETTING_STRUCT_CHANGE_PARAM):
        
        def __init__(self,setting_struct=None):
            SETTING_STRUCT_CHANGE_PARAM.__init__(self, setting_struct)
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
        
        def import_from_config(self, config,
                               ignore_errors=False,
                               try_fix_errors=False):
            # Read from section
            section = self.name
            
            value = config.get(section, "selected_value")
            
            # Should be expected integer value -> test it!
            try:
                value = int(value)
            except:
                msg = " Incorrect user value <"\
                                +str(value) +\
                                "> at option <"\
                                +str(self.name) +\
                                "> Expected type: integer\n"
                logger.error("[import_from_config]" + msg)
                # Check if we should raise exception or not
                if(ignore_errors == False):
                  raise Exception(msg)
                
                return
            # When value is number, then test for boundary conditions
            if(value < self.out_min):
              msg = " At option <{0}> is lower value than expected.\n"\
                    " Expected at "\
                    "least {1}, but got {2}.\n".format(self.name,
                                                       self.out_min,
                                                       value)
              # Check if we could fix problem
              if(try_fix_errors != False):
                msg = msg + " Value {0} will be used instead.\n".format(
                                                                self.out_min)
                value = self.out_min
                
                logger.warn("[import_from_config]" + msg)
              else:
                # Can not fix. Log error and check if throw exception
                logger.error("[import_from_config]" + msg)
                if(ignore_errors == False):
                  raise Exception(msg)
                else:
                  # Else ignore error. Just return
                  return
            
            if(value > self.out_max):
              msg = " At option <{0}> is higher value than expected.\n"\
                    " Expected at "\
                    "most {1}, but got {2}.\n".format(self.name,
                                                       out_max,
                                                       value)
              # Check if we could fix problem
              if(try_fix_errors != False):
                msg = msg + " Value {0} will be used instead.\n".format(
                                                                self.out_max)
                value = self.out_max
                
                logger.warn("[import_from_config]" + msg)
              else:
                # Can not fix. Log error and check if throw exception
                logger.error("[import_from_config]" + msg)
                if(ignore_errors == False):
                  raise Exception(msg)
                # Else ignore error. Just return
                return
            
            
            # OK, now value should be valid -> check if different
            if(self.out_value != value):
                self.out_value = value
                
                self.changed = True
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#


class BridgeConfigParser(object):
    # @brief: "Constants"
    # @{
    MAX_RETRY_CNT = 1
    # @}
    bridge = None
    
    
    ##
    # @brief Initialize procedure
    def __init__(self, VID, PID):
        self.VID = VID  # USB VendorID
        self.PID = PID  # USB ProductID
        
        
        
        
        self.s_cfg_settings = []
        
        # Try initialize Bridge
        retry_cnt = -1
        while(1):
            retry_cnt = retry_cnt +1
            
            if(retry_cnt > BridgeConfigParser.MAX_RETRY_CNT):
                logger.critical("[__init__]"
                                " Can not initialize Bridge\n")
                raise Exception(" Can not initialize Bridge")
            
            
            try:
              BridgeConfigParser.bridge = Bridge(self.VID, self.PID)
            
            except Exception as e:
                logger.error("[__init__][Bridge]" + str(e))
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
                    tmpst = GroupParam(setting)
                    groups[tmpst.name] = tmpst
                    logger.debug("[Init] Found group header: {0}\n".format(setting))
                else:
                    tmpst = SETTING_STRUCT_CHANGE_PARAM(setting)
                    
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
                    logger.debug("[__init__][Search groups] Found group item:"
                                  + str(setting) + "\n")
                    
                    # Add group to dictionary
                    groups[match_result.group(1)].add_choice_param(setting)
                    items_to_remove.append(setting)
                    
            #Remove duplicated items (this cannot be done in the for cycle above)
            for item in items_to_remove:
                temp.remove(item)
                    
            
            # And add all CMD ID for actual device to s_cfg_settings
            self.s_cfg_settings.append(temp)
        
        for DID in range(num_of_dev +1):
          for setting in BridgeConfigParser.bridge.get_all_settings[DID]:
            logger.debug("[__init__][Summary] {0}".format(setting))
        
        logger.info(" Actual configuration saved\n")
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
            config.add_comment(section,"Serial number: {0}".format(
                      BridgeConfigParser.bridge.device_metadata[DID].serial))
            
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
    #
    # @param filename: Name of file with extension from which settings will be
    #                  read
    # @param ignore_errors: When is set to non-zero value, then all errors in
    #                  configuration are ignored, but still logged. Simply:
    #                  when wrong configuration is detected, then just log
    #                  error and do NOT throw exception
    # @param try_fix_errors: When wrong configuration is occurred and there is
    #                  chance to "fix" value (find closest to allowed range)
    #                  then is logged only warning and value is changed to
    #                  valid
    def read_setting_from_file(self, filename,
                               ignore_errors=False,
                               try_fix_errors=False):
        # Initialize config parser
        config = ConfigParser.ConfigParser()
        
        status = config.read(filename)
        if(not status):
          msg = " Configuration file not found!"
          logger.error("[read_setting_from_file][config.read]" + msg)
          raise Exception(msg)
        
        logger.info("[read_setting_from_file] Configuration file opened\n")
        
        # Read setting by setting and compare if there is change. If yes, then
        # write change flag which will be used for sending new setting
        num_of_dev = BridgeConfigParser.bridge.get_max_Device_ID()
        for DID in range(num_of_dev +1):
            for setting in self.s_cfg_settings[DID]:
                setting.import_from_config(config,
                                           ignore_errors,
                                           try_fix_errors)
                if(setting.changed == True):
                    logger.debug("[read_setting_from_file] Changed <{0}>"
                                 " Actual value: {1}\n".format(setting.name,
                                                             setting.out_value))
        
        logger.info("[read_setting_from_file] All configuration items read\n")
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    ##
    # @brief Read processed s_cfg_settings and if there are any changes, then
    # will be send to AVR
    def write_setting_to_device(self):
      # Go thru all settings and check if "changed" flag is set
      num_of_dev = BridgeConfigParser.bridge.get_max_Device_ID()
      for DID in range(num_of_dev +1):
        for setting in self.s_cfg_settings[DID]:
          if(setting.changed == True):
            # Test if actual setting is normal item or group header
            if(setting.in_type == BridgeConfigParser.bridge.DATA_TYPES.group_type):
              # Group changed -> use CMD ID. Any other value is not needed
              # Device ID, Command ID, value=0 (not needed to write, default)
              BridgeConfigParser.bridge.set_setting_to_device(
                                                            DID,
                                                            setting.out_value)
              msg = "[write_setting_to_device] In group "
              msg = msg +"<{0}> was selected option {1}\n".format(
                                                            setting.name,
                                                            setting.out_value)
              logger.debug(msg)
            else:
              BridgeConfigParser.bridge.set_setting_to_device(
                                                      DID,
                                                      setting.CMD_ID,
                                                      setting.out_value)
              msg = "[write_setting_to_device] In item "
              msg = msg + "<{0}> was changed value to: {1}".format(
                                                      setting.name,
                                                      setting.out_value)
              logger.debug(msg)
      
      
      logger.info("[write_setting_to_device] Device configured\n")
    
#-----------------------------------------------------------------------------#
#                                                                             #
#-----------------------------------------------------------------------------#
    def close_device(self):
      BridgeConfigParser.bridge.close()

