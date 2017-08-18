"""
.. module:: concon.structs
    :platform: Unix, Windows
    :synopsis: Classes for description configuration/setting structures.
.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>

"""

from .HW_bridge_uniprot import DataTypes
from .descriptor_parser import process_descriptor_for_configfile
import logging

logger = logging.getLogger(__name__)


# Structure for get/set setting functions
class SettingStruct(object):
    def __init__(self):
        self.in_type = -1
        self.in_min = -1
        self.in_max = -1
        self.out_type = -1
        self.out_min = -1
        self.out_max = -1
        self.out_value = -1
        self.name = ""
        self.descriptor = ""

    def __str__(self):
        return " NAME: {0}\n" \
               " DESCRIPTOR: {1}\n IN TYPE: {2}\n IN MIN:" \
               " {3}\n IN MAX: " \
               "{4}\n OUT TYPE: {5}\n OUT MIN: {6}\n OUT MAX: {7}\n " \
               "OUT VALUE: {8}\n" \
            .format(self.name,
                    self.descriptor,
                    DataTypes.data_type_to_str(self.in_type),
                    self.in_min, self.in_max,
                    DataTypes.data_type_to_str(self.out_type),
                    self.out_min, self.out_max,
                    self.out_value)


class SettingStructChangeParam(SettingStruct):
    # Define how many digits will be displayed/saved to file
    FLOAT_PRECISION = 3

    def __init__(self, setting_struct=None):
        SettingStruct.__init__(self)
        # If parameter setting_struct exist (is given)
        if setting_struct:
            # Then just update structure
            self.__dict__.update(setting_struct.__dict__)

        # Extra variables

        # Just for checking if variable was changed in cfg file
        self.changed = False
        # In some cases is useful when CMD_ID is also stored in memory
        self.CMD_ID = -1

    def __str__(self):
        return super(SettingStructChangeParam, self).__str__() + \
               " Changed: {0}\n CMD ID: {1}\n".format(self.changed, self.CMD_ID)

    def export_to_config(self, config, did):

        # Create section
        section = str(did) + ": " + self.name
        config.add_section(section)

        # If there is some descriptor -> add it!
        if self.descriptor != "":
            comment = process_descriptor_for_configfile(
                self.descriptor)
            config.add_comment(section, comment)

        # Test for input and output type is void
        if ((self.in_type == self.out_type) and
                (self.in_type == DataTypes.VOID)):
            comment = "Set call_function to non zero if you want call" \
                      " this function"
            config.add_comment(section, comment)
            config.set(section, "call_function", "0")

        # Else test only for input void (there is non-void output)
        elif self.in_type == DataTypes.VOID:
            comment = "OUT TYPE: {0} < {1} : {2} > | value: {3}".format(
                DataTypes.data_type_to_str(self.out_type),
                self.out_min,
                self.out_max,
                self.out_value)
            config.add_comment(section, comment)
            comment = "Set call_function to non zero if you want call" \
                      " this function"
            config.add_comment(section, comment)
            config.set(section, "call_function", "0")

        # Test if just output type is void - again different format and
        # comments
        elif self.out_type == DataTypes.VOID:
            comment = "IN TYPE: {0} < {1} : {2} >".format(
                DataTypes.data_type_to_str(self.in_type),
                self.in_min,
                self.in_max)
            config.add_comment(section, comment)
            config.set(section, "value", "not changed")

        # Now compare IN TYPE and OUT TYPE and if they have same range
        elif ((self.in_type == self.out_type) and
              (self.in_min == self.out_min) and
              (self.in_max == self.out_max)):
            # If equal - just add comment with data type, min, max and
            # actual value

            # Test if data type is float. Then round it
            if self.in_type == DataTypes.FLOAT:
                self.in_min = format(round(self.in_min, self.FLOAT_PRECISION))
                self.in_max = format(round(self.in_max, self.FLOAT_PRECISION))
                self.out_value = \
                    format(round(self.out_value, self.FLOAT_PRECISION))

            comment = "TYPE: {0} < {1} : {2} > | current value: {3}".format(
                DataTypes.data_type_to_str(self.in_type),
                self.in_min,
                self.in_max,
                self.out_value)

            config.add_comment(section, comment)

            config.set(section, "value", str(self.out_value))

        # Else just write in and out type, out value
        else:
            # Test if data type is float. Then round it
            if self.in_type == DataTypes.FLOAT:
                self.in_min = format(round(self.in_min, self.FLOAT_PRECISION))
                self.in_max = format(round(self.in_max, self.FLOAT_PRECISION))
                self.out_min = format(
                    round(self.out_min, self.FLOAT_PRECISION))
                self.out_max = format(round(self.out_max,
                                            self.FLOAT_PRECISION))
                self.out_value = format(round(self.out_value,
                                              self.FLOAT_PRECISION))

            comment = "IN TYPE: {0} < {1} : {2} >".format(
                DataTypes.data_type_to_str(self.in_type),
                self.in_min,
                self.in_max)
            config.add_comment(section, comment)
            comment = "OUT TYPE: {0} < {1} : {2} > | out value: {3}".format(
                DataTypes.data_type_to_str(self.out_type),
                self.out_min,
                self.out_max,
                self.out_value)
            config.add_comment(section, comment)

            config.set(section, "in_value", "not changed")

    def import_from_config(self, config, did, ignore_errors=False,
                           try_fix_errors=False):
        # Check for error input types
        if self.in_type == DataTypes.GROUP:
            msg = " Invalid data type: group. Internal error\n"
            logger.error("[import_from_config]" + msg)
            raise Exception(msg)

        # Find section
        section = str(did) + ": " + self.name

        # According to actual input and output data types choose correct
        # variable name

        # Test if input type is void
        if self.in_type == DataTypes.VOID:
            # Input and output types are void -> check if function should
            # be called
            value = config.get(section, "call_function")
            if value != "0":
                # Function should be called -> value changed
                self.out_value = "Call function"

                self.changed = True

            # Nothing to do here -> return
            return

        # Test if just output type is void - again different format and
        # comments
        elif self.out_type == DataTypes.VOID:
            # Output is void, so we can not know what value was last.
            # However if there were some change, then "value" should be
            # different than "not changed"

            # Load value
            value = config.get(section, "value")

            # Check if value was not changed
            if value == "not changed":
                return

        # Test for same data types and values
        elif ((self.out_type == self.in_type) and
              (self.in_min == self.out_min) and
              (self.in_max == self.out_max)):

            value = config.get(section, "value")
            # Check if value is different according to data type

            # check if value is number or string/char
            try:
                value = float(value)
            except ValueError:
                # If fail -> string -> check data IN TYPE with char (only
                # correct option). If not char -> user fail -> error
                if self.in_type != DataTypes.CHAR:
                    msg = " Incorrect user value <{0}> at option <{1}>" \
                          " Expected type {2}\n".format(
                            value,
                            self.name,
                            DataTypes.data_type_to_str(self.in_type))
                    logger.error("[import_from_config]" + msg)

                    if not ignore_errors:
                        raise Exception(msg)
                    return
                # Else value is character -> change it!
                else:

                    # Test if there is more characters -> if yes, then
                    # log problem and if needed raise exception

                    if ignore_errors:
                        # Just inform user that there is problem
                        msg = " In option <{0}> expected only one " \
                              "character, but found string. Using only " \
                              "first character <{1}>".format(self.name,
                                                             value[0])
                        logger.warn(msg)
                    else:
                        # Well, else we can not let problem as it as.
                        # Throw exception and log problem
                        msg = " In option <{0}> expected only one " \
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
            if self.out_value == value:
                # If they are same -> nothing to do -> return
                return

        # Last option: different data types are same
        else:
            value = config.get(section, "in_value")

            # Check if value was changed
            if value == "not changed":
                return

        # Almost done...

        try:
            value = float(value)
        except ValueError:
            # When fail -> value is string
            # Check for char type -> else there is problem
            if self.in_type != DataTypes.CHAR:
                msg = " Incorrect user value <{0}> at option <{1}>. " \
                      "Expected type: {2}\n".format(
                        value,
                        self.name,
                        DataTypes.data_type_to_str(self.in_type))
                logger.error("[import_from_config]" + msg)

                # This problem can not be fixed. But we can ignore this
                # error, or raise exception
                if not ignore_errors:
                    raise Exception(msg)
                # Else no exception -> just return
                else:
                    return

        # Retype (if needed) value according to input type
        if ((self.in_type != DataTypes.FLOAT) and
                (DataTypes.CHAR != self.in_type)):
            value = int(value)

        # Check boundaries
        if value < self.in_min:
            msg = " At option <{0}> is lower value than" \
                  " expected!\n Expected at least {1} but got {2}.\n".format(
                    self.name,
                    self.in_min,
                    value)

            # Check if we can fix errors
            if try_fix_errors:
                # Can fix -> use minimum -> expand message
                msg = msg + " Value {0} will be used instead.\n".format(
                    self.in_min)
                logger.warn("[import_from_config]" + msg)
                value = self.in_min
            else:
                # Can not fix -> raise exception or just throw this setting
                logger.error("[import_from_config]" + msg)

                if not ignore_errors:
                    # No error allowed -> Throw exception
                    raise Exception(msg)
                return

        if value > self.in_max:
            msg = " At option <{0}> is higher value than" \
                  " expected!\n Expected at most {1} but got {2}.\n".format(
                    self.name,
                    self.in_max,
                    value)

            # Check if we can fix errors
            if try_fix_errors:
                # Can fix -> use minimum -> expand message
                msg = msg + " Value {0} will be used instead.\n".format(
                    self.in_max)
                logger.warn("[import_from_config]" + msg)
                value = self.in_max
            else:
                # Can not fix -> raise exception or just throw this setting
                logger.error("[import_from_config]" + msg)

                if not ignore_errors:
                    # No error allowed -> Throw exception
                    raise Exception(msg)
                return

        # Write value
        self.out_value = value
        # Value changed
        self.changed = True

        return


class GroupParam(SettingStructChangeParam):
    def __init__(self, setting_struct=None):
        SettingStructChangeParam.__init__(self, setting_struct)
        self._choice_params = []

    def add_choice_param(self, param):
        self._choice_params.append(param)

    def export_to_config(self, config, did):
        # Create section
        section = str(did) + ": " + self.name
        config.add_section(section)
        config.add_comment(section, self.descriptor)
        config.add_comment(section,
                           "TYPE: {0} < {1} : {2} > | current value: {3} |"
                           " Available choices:".format(
                               DataTypes.data_type_to_str(self.out_type),
                               self.out_min,
                               self.out_max,
                               self.out_value))
        for choice_param in self._choice_params:
            # Test if data type is void or not
            if choice_param.out_type == DataTypes.VOID:

                # Test if descriptor is empty. If yes, then show at
                # least name
                if choice_param.descriptor == "":
                    config.add_comment(section, "{id}: {description}".format(
                        description=choice_param.name,
                        id=choice_param.CMD_ID))
                else:
                    config.add_comment(section, "{id}: {description}".format(
                        description=choice_param.descriptor,
                        id=choice_param.CMD_ID))
            else:
                # Test if descriptor is empty. If yes, then show at
                # least name
                if choice_param.descriptor == "":
                    config.add_comment(
                        section,
                        "{id}: {description} | return: {val}".format(
                            description=choice_param.name,
                            id=choice_param.CMD_ID,
                            val=choice_param.out_value))
                else:
                    config.add_comment(
                        section,
                        "{id}: {description} | return: {val}".format(
                            description=choice_param.descriptor,
                            id=choice_param.CMD_ID,
                            val=choice_param.out_value))
        # out value
        config.set(section, "selected_value", str(self.out_value))

    def import_from_config(self, config,
                           did,
                           ignore_errors=False,
                           try_fix_errors=False):
        # Read from section
        section = str(did) + ": " + self.name

        value = config.get(section, "selected_value")

        # Should be expected integer value -> test it!
        try:
            value = int(value)
        except ValueError:
            msg = " Incorrect user value <" \
                  + str(value) + \
                  "> at option <" \
                  + str(self.name) + \
                  "> Expected type: integer\n"
            logger.error("[import_from_config]" + msg)
            # Check if we should raise exception or not
            if not ignore_errors:
                raise Exception(msg)

            return
        # When value is number, then test for boundary conditions
        if value < self.out_min:
            msg = " At option <{0}> is lower value than expected.\n" \
                  " Expected at " \
                  "least {1}, but got {2}.\n".format(self.name,
                                                     self.out_min,
                                                     value)
            # Check if we could fix problem
            if try_fix_errors:
                msg = msg + " Value {0} will be used instead.\n".format(
                    self.out_min)
                value = self.out_min

                logger.warn("[import_from_config]" + msg)
            else:
                # Can not fix. Log error and check if throw exception
                logger.error("[import_from_config]" + msg)

                if not ignore_errors:
                    raise Exception(msg)
                else:
                    # Else ignore error. Just return
                    return

        if value > self.out_max:
            msg = " At option <{0}> is higher value than expected.\n" \
                  " Expected at " \
                  "most {1}, but got {2}.\n".format(self.name,
                                                    self.out_max,
                                                    value)
            # Check if we could fix problem
            if try_fix_errors:
                msg = msg + " Value {0} will be used instead.\n".format(
                    self.out_max)
                value = self.out_max

                logger.warn("[import_from_config]" + msg)
            else:
                # Can not fix. Log error and check if throw exception
                logger.error("[import_from_config]" + msg)

                if not ignore_errors:
                    raise Exception(msg)
                # Else ignore error. Just return
                return

        # OK, now value should be valid -> check if different
        if self.out_value != value:
            self.out_value = value

            self.changed = True
