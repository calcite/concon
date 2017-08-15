# -*- coding: utf-8 -*-
"""

"""
import re
from .parser_utils import ConfigParserWithComments
from structs import SettingStructChangeParam, GroupParam

from HW_bridge_uniprot import *

if sys.version_info[0] == 2:
    import ConfigParser as configparser
elif sys.version_info[0] == 3:
    import configparser
else:
    raise Exception("Unknown python version")

##
# @file
# @brief Python script for configuration parser
#
# Created:  31.03.2014
# Modified: 20.06.2014
#
# @author Martin Stejskal

# For detection python version (2 or 3)

##
# @brief For logging events


##
# @brief Get logging variable
logger = logging.getLogger('Bridge config parser')


class BridgeConfigParser(object):
    MAX_RETRY_CNT = 3

    def __init__(self, vid, pid):
        self.VID = vid  # USB VendorID
        self.PID = pid  # USB ProductID
        self._bridge = None
        self._s_cfg_settings = []

        # Try initialize Bridge
        retry_cnt = -1
        while True:
            retry_cnt = retry_cnt + 1

            if retry_cnt > BridgeConfigParser.MAX_RETRY_CNT:
                logger.critical("[__init__]"
                                " Can not initialize Bridge\n")
                raise Exception(" Can not initialize Bridge")

            try:
                self._bridge = Bridge(self.VID, self.PID)

            except IOError as e:
                logger.error("[__init__][Bridge]" + str(e))
                continue

            else:
                break

        logger.info(" All configurations from device downloaded\n")

        # Copy whole settings to array s_cfg_settings - go thru all devices
        num_of_dev = self._bridge.get_max_device_id()

        for did in range(num_of_dev + 1):
            # Copy thru all commands
            # Get max CMD ID for actual device

            # Temporary array for settings
            temp = []

            # Dictionary for groups (CMD_ID and "group name")
            groups = {}

            cnt = 0
            # Go thru all CMD_ID
            for setting in self._bridge.all_settings[did]:

                # Test if group header found
                if setting.in_type == Bridge.DATA_TYPES.group_type:
                    # Create key in dictionary (will be filled later)
                    tmpst = GroupParam(setting)
                    groups[tmpst.name] = tmpst
                    logger.debug(
                        "[Init] Found group header: {0}\n".format(setting))
                else:
                    tmpst = SettingStructChangeParam(setting)

                # Anyway: always set changed variable to false (so far
                # nothing was changed)
                tmpst.changed = False

                tmpst.CMD_ID = cnt

                # Add to temp array
                temp.append(tmpst)

                cnt = cnt + 1

            items_to_remove = []
            for setting in temp:
                # Compare with group pattern
                match_result = re.match("{([a-zA-Z0-9_ ]+)}",
                                        setting.name)

                # If match -> add actual setting move to groups
                if match_result:
                    logger.debug("[__init__][Search groups] Found group item:"
                                 + str(setting) + "\n")

                    # Add group to dictionary
                    groups[match_result.group(1)].add_choice_param(setting)
                    items_to_remove.append(setting)

            # Remove duplicated items (this cannot be done in the for cycle
            # above)
            for item in items_to_remove:
                temp.remove(item)

            # And add all CMD ID for actual device to s_cfg_settings
            self._s_cfg_settings.append(temp)

        for did in range(num_of_dev + 1):
            for setting in self._bridge.all_settings[did]:
                logger.debug("[__init__][Summary] {0}".format(setting))

        logger.info(" Actual configuration saved\n")

        # --------------------------------------------------------------------#

    # ------------------------------------------------------------------------#
    ##
    # @brief Write loaded settings from bridge to file
    def write_setting_to_cfg_file(self, filename):
        # Initialize config parser
        config = ConfigParserWithComments()

        num_of_dev = self._bridge.get_max_device_id()

        for DID in range(num_of_dev + 1):
            section = self._bridge.device_metadata[DID].descriptor
            # Because on one device can be multiple drivers there is prefix
            section = str(DID) + ": " + section
            config.add_section(section)
            config.add_comment(section, "Device ID (DID): " + str(DID))
            config.add_comment(section, "Serial number: {0}".format(
                self._bridge.device_metadata[DID].serial))

            # Go thru command by command in device (DID)
            for setting in self._s_cfg_settings[DID]:
                setting.export_to_config(config, DID)

        # Write configuration data to file
        with open(filename, 'wb') as configfile:
            config.write(configfile)

        logger.info("[write_setting_to_cfg_file] Data written to file\n")

    # ------------------------------------------------------------------------#
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
        config = configparser.ConfigParser()

        status = config.read(filename)
        if not status:
            msg = " Configuration file not found!"
            logger.error("[read_setting_from_file][config.read]" + msg)
            raise Exception(msg)

        logger.info("[read_setting_from_file] Configuration file opened\n")

        # Read setting by setting and compare if there is change. If yes, then
        # write change flag which will be used for sending new setting
        num_of_dev = self._bridge.get_max_device_id()

        for did in range(num_of_dev + 1):

            for setting in self._s_cfg_settings[did]:
                setting.import_from_config(config, did, ignore_errors,
                                           try_fix_errors)

                if setting.changed:
                    logger.debug("[read_setting_from_file] Changed <{0}>"
                                 " Actual value: {1}\n".format(
                                        setting.name, setting.out_value))

        logger.info("[read_setting_from_file] All configuration items read\n")

    # -------------------------------------------------------------------------#
    ##
    # @brief Read processed s_cfg_settings and if there are any changes, then
    # will be send to AVR
    def write_setting_to_device(self):
        # Go through all settings and check if "changed" flag is set
        num_of_dev = self._bridge.get_max_device_id()

        for did in range(num_of_dev + 1):

            for setting in self._s_cfg_settings[did]:

                if setting.changed:

                    # Test if actual setting is normal item or group header
                    if setting.in_type == Bridge.DATA_TYPES.group_type:

                        # Group changed -> use CMD ID. Any other value
                        # is not needed
                        # Device ID, Command ID, value=0 (not needed to write,
                        # default)
                        self._bridge.set_setting_to_device(
                            did, setting.out_value)
                        msg = "[write_setting_to_device] In group "
                        msg = msg + "<{0}> was selected option {1}\n".format(
                            setting.name,
                            setting.out_value)
                        logger.debug(msg)
                    else:
                        self._bridge.set_setting_to_device(
                            did, setting.CMD_ID, setting.out_value)
                        msg = "[write_setting_to_device] In item "
                        msg = msg + "<{0}> was changed value to: {1}".format(
                            setting.name, setting.out_value)
                        logger.debug(msg)

        logger.info("[write_setting_to_device] Device configured\n")

    # ------------------------------------------------------------------------#
    def close_device(self):
        self._bridge.close()
