# -*- coding: utf-8 -*-
"""
.. module:: concon.HW_bridge_uniprot
    :synopsis: Bridge between uniprot and higher layer from generic driver.
.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>

Functions for higher layer:

.. code-block:: python

     # Do initialization
     bridge = Bridge()    # Initialization and download metadata

     # Get number of max Device_ID (used index)
     max_DID = bridge.get_max_Device_ID()

     # Get downloaded metadata. User can select device thru index. Maximum index
     # is max_DID.
     print(bridge.get_metadata[max_DID])

     bridge.close()  # should be called when no communication is needed
                     # (at the end of program)

"""

from .uniprot import *
from .core import ConConError

# For binary operation
import struct

# For python version detection
import sys

##
# @brief Get logging variable
logger = logging.getLogger('Bridge HW <---> uniprot')


class BridgeException(ConConError):
    pass


class BridgeDeviceNotFound(BridgeException):
    pass


class BridgeDeviceReconnect(BridgeException):
    pass


class BridgeDeviceRxBufferOverflow(BridgeException):
    pass


class BridgeNackFail(BridgeException):
    pass


class BridgeResetFail(BridgeException):
    pass


class BridgeError(BridgeException):
    pass


class ResCodes(object):
    SUCCESS = 0
    FAIL = 1
    INCORRECT_PARAMETER = 2
    INCORRECT_CMD_ID = 3
    CMD_ID_NOT_EQUAL_IN_FLASH = 4
    INCORRECT_DEVICE_ID = 5

    STRINGS = {SUCCESS: "Success",
               FAIL: "Fail",
               INCORRECT_PARAMETER: "Incorrect input parameter",
               INCORRECT_CMD_ID: "Incorrect CMD ID",
               INCORRECT_DEVICE_ID: "Incorrect Device ID",
               CMD_ID_NOT_EQUAL_IN_FLASH:
                   "CMD ID is not equal with CMD ID found at flash on device",
               }

    @classmethod
    def code_to_string(cls, code):
        """ Convert result code number to string.

        :param code:  Code ID/number.
        :return: Result code string.
        """
        return cls.STRINGS.get(code,
                               "Unknown error. Please update software "
                               "with device version")


# This definitions must be same on AVR too!
class DataTypes(object):
    VOID = 0
    CHAR = 1
    INT = 2
    INT8 = 3
    INT16 = 4
    INT32 = 5
    UINT = 6
    UINT8 = 7
    UINT16 = 8
    UINT32 = 9
    FLOAT = 10
    GROUP = 11

    STRINGS = {VOID: "void",
               CHAR: "char",
               INT: "int (32b)",
               INT8: "int8",
               INT16: "int16",
               INT32: "int32",
               UINT: "uint (32b)",
               UINT8: "uint8",
               UINT16: "uint16",
               UINT32: "uint32",
               FLOAT: "float",
               GROUP: "group"
               }

    @classmethod
    def data_type_to_str(cls, i_data_type):
        """ Convert data type number to string.

        :param i_data_type:  Code for data type
        :return:
        """
        return cls.STRINGS.get(
            i_data_type, "Unknown data type. Please update software "
                         "with device version")


class BridgeMetadata(object):
    """ Dynamic structure for metadata. Default should be invalid values.
    """
    def __init__(self):
        self.max_cmd_id = -1
        self.serial = -1
        self.descriptor = ""

    def __str__(self):
        return " {0}\n Serial: {1}\n Max CMD ID: {2}\n" \
               "<------------------------>" \
            .format(self.descriptor, self.serial, self.max_cmd_id)


class Bridge(object):
    MAX_RETRY_CNT = 3

    # In some cases should be defined maximum size of RX buffer
    MAX_RX_BUFFER_BYTES = 65530

    # Following constants must be same as in firmware (HW_bridge_uniprot)
    STATE_WAITING_FOR_REQUEST = 0
    STATE_REQUEST_GET_SETTING = 1
    STATE_REQUEST_SET_SETTING = 2
    STATE_REQUEST_GET_METADATA = 3
    STATE_REQUEST_GET_NUM_OF_DEV = 4
    STATE_SEND_ONLY_RETURN_CODE = 5
    STATE_SEND_RETURN_CODE_AND_METADATA = 6
    STATE_SEND_RETURN_CODE_AND_SETTING = 7

    def __init__(self, vid, pid, timeout, progress_bar=None):
        """ Connect to the target device if possible.

        :param vid:  USB VID
        :param pid:  USB PID
        """
        self.vid = vid  # USB VendorID
        self.pid = pid  # USB ProductID

        # Number of detected devices (-1 -> error -> so far none)
        self.i_num_of_devices = -1
        self._uniprot = None

        try:
            logger.debug("[__init__] Trying initialize uniprot")
            self._uniprot = Uniprot(self.vid, self.pid, timeout=timeout)
            logger.debug("[__init__] Getting num. of devices")
            self.get_number_of_devices_from_device()

        except UniprotExceptionDeviceNotFound as e:
            logger.error("[__init__][Uniprot init]" + str(e))
            raise BridgeDeviceNotFound("[Uniprot init]" +
                                       str(e))

        except BridgeDeviceNotFound as e:
            logger.error("[__init__][Get num of dev]" + str(e))
            raise UniprotExceptionDeviceNotFound("[Get num of dev]" +
                                                 str(e))

        except BridgeDeviceRxBufferOverflow as e:
            logger.critical("[__init__][Get num of dev]" + str(e))
            raise BridgeDeviceRxBufferOverflow("[Get num of dev]"
                                               + str(e))

        except BridgeNackFail as e:
            logger.critical("[__init__][Get num of dev]" + str(e))
            raise BridgeNackFail("[Get num of dev]" + str(e))

        except BridgeResetFail as e:
            logger.critical("[__init__][Get num of dev]" + str(e))
            raise BridgeResetFail("[Get num of dev]" + str(e))

        # Try to get all metadata and save them to array
        self.s_metadata = []
        for i in range(self.i_num_of_devices + 1):
            try:
                logger.debug("[__init__] Getting metadata from device")
                self.s_metadata.append(self.get_metadata_from_device(i))
            except BridgeDeviceNotFound as e:
                logger.error("[__init__][Get metadata]" + str(e))
                raise BridgeDeviceNotFound("[Get metadata]" +
                                           str(e))

            except BridgeDeviceRxBufferOverflow as e:
                logger.critical("[__init__][Get metadata]" + str(e))
                raise BridgeDeviceRxBufferOverflow(
                    "[Get metadata]" + str(e))

            except BridgeNackFail as e:
                logger.critical("[__init__][Get metadata]" + str(e))
                raise BridgeNackFail("[Get metadata]" + str(e))

            except BridgeResetFail as e:
                logger.critical("[__init__][Get metadata]" + str(e))
                raise BridgeResetFail("[Get metadata]" + str(e))

        # Show devices thru saved metadata
        for i in range(self.i_num_of_devices + 1):
            logger.info("[__init__]" + str(self.s_metadata[i]))

        # Load actual configuration from device to RAM
        self.s_settings_in_RAM = []

        # Optional progressbar update
        if progress_bar:
            total_length = 0
            for i_DID in range(self.i_num_of_devices + 1):
                total_length += self.s_metadata[i_DID].max_cmd_id + 1
            progress_bar.length = total_length

        # Go thru all devices
        for i_DID in range(self.i_num_of_devices + 1):
            # Thru all commands

            temp = []
            for i_CMD_ID in range(self.s_metadata[i_DID].max_cmd_id + 1):
                try:
                    logger.debug("[__init__] Trying to get setting from device"
                                 "{0} (CMD: {1})".format(i_DID, i_CMD_ID))
                    temp.append(
                        self.get_setting_from_device(i_DID, i_CMD_ID))

                    if progress_bar:
                        progress_bar.update(1)

                # And check all exceptions
                except BridgeDeviceNotFound as e:
                    logger.error("[__init__][Get setting]" + str(e))
                    raise BridgeDeviceNotFound("[Get setting]"
                                               + str(e))

                except BridgeDeviceRxBufferOverflow as e:
                    logger.error("[__init__][Get setting]" + str(e))
                    raise BridgeDeviceRxBufferOverflow(
                        "[Get metadata]" + str(e))

                except BridgeNackFail as e:
                    logger.critical("[__init__][Get setting]" + str(e))
                    raise BridgeNackFail("[Get setting]" + str(e))

                except BridgeResetFail as e:
                    logger.critical("[__init__][Get setting]" + str(e))
                    raise BridgeResetFail("[Get setting]" + str(e))

                except Exception as e:
                    logger.error("[__init__][Get setting] " + str(e))

                # If OK, then show info
                logger.info("[__init__][Get setting] "
                            "Get setting from DID: " + str(i_DID) +
                            " | CMD ID: " + str(i_CMD_ID) + " OK\n")

            self.s_settings_in_RAM.append(temp)

        for i_DID in range(self.i_num_of_devices + 1):
            for i_CMD_ID in range(self.s_metadata[i_DID].max_cmd_id + 1):
                logger.debug("DID: " + str(i_DID) + " | CMD: "
                             + str(i_CMD_ID) + "\n" +
                             str(self.s_settings_in_RAM[i_DID][i_CMD_ID]))

    def close(self):
        """ Close device (stop using USB interface).
        """
        try:
            self._uniprot.close()
            logger.info("[close] Device closed")
        except UniprotExceptionDeviceNotFound as e:
            # Even if this exception occurs, program can re-initialize device
            # if needed
            logger.error("[close][Uniprot close] " + str(e))
            raise BridgeDeviceNotFound("[Uniprot close] " + str(e))

    @staticmethod
    def get_signed_number(number, bit_length):
        mask = (2 ** bit_length) - 1
        if number & (1 << (bit_length - 1)):
            return number | ~mask
        else:
            return number & mask

    @staticmethod
    def get_float_number(number):
        # Create byte array from unsigned integer
        temp_bytes = struct.pack('I', number)
        # Convert temp_bytes to float
        temp_float = struct.unpack('f', temp_bytes)
        # Return just first float number (just 4 case)
        return temp_float[0]

    def retype(self, i_value, i_data_type):
        """ Convert variable to correct data type.

        Because uniprot send data as byte stream it is up to this layer to
        retype variables back to origin type

        :param i_value: Value to by type-cast.
        :param i_data_type: Type to cast to.
        :return: Type-casted value.
        """
        if i_data_type == DataTypes.CHAR:
            # This is python version dependent
            if sys.version_info[0] == 2:
                return str(unichr(i_value))
            elif sys.version_info[0] == 3:
                return str(chr(i_value))
            else:
                raise BridgeError("Unsupported python version")

        if i_data_type == DataTypes.FLOAT:
            return self.get_float_number(i_value)

        if i_data_type == DataTypes.INT16:
            return self.get_signed_number(i_value, 16)

        if i_data_type == DataTypes.INT32:
            return self.get_signed_number(i_value, 32)

        if i_data_type == DataTypes.INT8:
            return self.get_signed_number(i_value, 8)

        if i_data_type == DataTypes.INT:
            return self.get_signed_number(i_value, 32)

        if i_data_type == DataTypes.UINT16:
            return i_value

        if i_data_type == DataTypes.UINT32:
            return i_value

        if i_data_type == DataTypes.UINT8:
            return i_value

        if i_data_type == DataTypes.UINT:
            return i_value

        if i_data_type == DataTypes.VOID:
            return None

        if i_data_type == DataTypes.GROUP:
            return i_value
        else:
            message = "[retype] Unknown data type (" + str(i_data_type) + \
                      ")\n"
            logger.error(message)

    def send_request_get_data(self, i_tx_buffer):
        """ Send request and get response.

        TX packet and RX packet must be configured before call this function

        :param i_tx_buffer:  Data to send.
        :return:  received data.
        """
        # Reset retry count
        i_retry_cnt = 0

        i_rx_buffer = None

        # Inform if request should be transmitted again
        # send_request_again = 0

        # Main loop - TX data + RX data
        while True:
            # Reset value -> request will be send anyway (next while)
            send_request_again = 0
            # Secondary loop - try TX data

            while True:
                if i_retry_cnt > 0:
                    logger.warn("[send_request_get_data][Uniprot TX data]"
                                " Retry count: " + str(i_retry_cnt) + "\n")
                try:
                    # Try to send request
                    status = self._uniprot.usb_tx_data(i_tx_buffer)

                except UniprotExceptionDeviceNotFound as e:
                    logger.error("[send_request_get_data]"
                                 "[Uniprot TX data]"
                                 + str(e))
                    raise BridgeDeviceNotFound("[Uniprot TX data]"
                                               + str(e))

                except UniprotExceptionNackFail as e:
                    logger.critical("[send_request_get_data]"
                                    "[Uniprot TX data]"
                                    + str(e))
                    raise BridgeNackFail("[Uniprot TX data]"
                                         + str(e))

                except UniprotExceptionRxBufferOverflow as e:
                    logger.critical("[send_request_get_data]"
                                    "[Uniprot TX data]"
                                    + str(e))
                    raise BridgeDeviceRxBufferOverflow("[Uniprot TX data]"
                                                       + str(e))

                except UniprotExceptionResetSuccess as e:
                    logger.warn("[send_request_get_data]"
                                "[Uniprot TX data]"
                                + str(e))
                    # Send data once again, but first clear input buffers.
                    # Wait until 5 dummy time-out packets received
                    self._uniprot.usb_clear_rx_buffer(5)

                    # And then try
                    i_retry_cnt = i_retry_cnt + 1
                    if i_retry_cnt > Bridge.MAX_RETRY_CNT:
                        logger.critical("[send_request_get_data]"
                                        " Reset retry count reach"
                                        "maximum (TX data).\n")
                        raise BridgeResetFail("Reset retry count reach maximum"
                                              " (TX data).\n")
                else:
                    # Else TX data without exception -> break while
                    break

            logger.debug("[send_request_get_data]"
                         " Request status: " + status + "\n")

            # Secondary loop - try RX data

            # RX data (one setting)
            while True:
                if i_retry_cnt > 0:
                    logger.warn("[send_request_get_data][Uniprot RX data]"
                                " Retry count: " + str(i_retry_cnt) + "\n")
                try:
                    i_rx_buffer = self._uniprot.usb_rx_data()
                except UniprotExceptionDeviceNotFound as e:
                    logger.error("[send_request_get_data][Uniprot RX data]"
                                 + str(e))
                    raise BridgeDeviceNotFound("[Uniprot RX data]"
                                               + str(e))
                except UniprotExceptionResetSuccess as e:
                    logger.warn("[send_request_get_data][Uniprot RX data]"
                                + str(e))

                    # Send data once again, but first clear input buffers.
                    # Wait until 5 dummy time-out packets received
                    self._uniprot.usb_clear_rx_buffer(5)

                    i_retry_cnt = i_retry_cnt + 1
                    if i_retry_cnt > Bridge.MAX_RETRY_CNT:
                        logger.critical("[send_request_get_data]"
                                        "[Uniprot RX data]"
                                        " Reset retry count"
                                        " reach maximum (RX data).\n")
                        raise BridgeResetFail("Reset retry count reach maximum"
                                              " (RX data).\n")
                    else:
                        # Must send request again (reset was done, so
                        # everything is set to default -> request was removed.
                        # So, set send_request_again to 1 and break this while
                        # to get to TX while
                        send_request_again = 1
                        break
                else:
                    # Else no exception -> break while
                    break
            # Test if all OK (send_request_again = 0) or if request should be
            # send once again due to reset
            if send_request_again == 0:
                # If all OK -> break even main while cycle
                break

        # If all OK -> return RX data
        return i_rx_buffer

    def get_number_of_devices_from_device(self):
        """ Try to get number of devices connected to target.

        :return:  Number of detected devices connected to target.
        """
        # Fill TX buffer
        i_tx_buffer = [0x00] * 2
        # Device ID - ALWAYS MUST BE 0 !!!
        i_tx_buffer[0] = 0x00
        # Bridge command (request number)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_NUM_OF_DEV

        # Configure TX packet
        self._uniprot.config_tx_packet(2)

        # Configure RX packet (expect 3B)
        self._uniprot.config_rx_packet(3)

        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeDeviceNotFound as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeDeviceNotFound(message)

        except BridgeNackFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeNackFail(message)

        except BridgeDeviceRxBufferOverflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeDeviceRxBufferOverflow(message)

        except BridgeResetFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_number_of_devices_from_device]" + message)
            raise BridgeResetFail(message)

        # Test if send Device ID is correct
        if i_rx_buffer[0] != 0:
            # This should not happen. It is not big problem, but it is not
            # standard behaviour
            logger.warn("[get_number_of_devices_from_device]"
                        "[Uniprot RX data] Device ID is not 0x00!")

        # Test if there is some problem on AVR side
        if i_rx_buffer[1] == 0:
            # No problem, everything works

            self.i_num_of_devices = i_rx_buffer[2]
            # Send only number of devices (max. device index number)
            return i_rx_buffer[2]

        logger.error("[get_number_of_devices_from_device]"
                     " Error code from AVR is not 0, but it should be!"
                     " Error: " + ResCodes.code_to_string(i_rx_buffer[1])
                     + "\n")

        # Else exception - this never should happen
        raise BridgeError(" Error code from AVR is not 0, but it should be!\n")

    def get_metadata_from_device(self, i_device_id):

        # Check if Device ID is valid
        if i_device_id > self.i_num_of_devices:
            message = " Invalid Device ID. "
            if self.i_num_of_devices < 0:
                message = message + "It looks that bridge was not " \
                                    "initialized. Please call function" \
                                    " Uniprot_init() and check " \
                                    "all exceptions.\n"
            else:
                # It look that bridge was initialized, but Device ID is invalid
                message = message + "Maximum Device ID is " + \
                          str(self.i_num_of_devices) + " .\n"

            logger.warn("[get_metadata_from_device]" + message)

            raise BridgeError(message)

        # Fill TX buffer by zeros
        i_tx_buffer = [0x00] * 2
        # Device ID
        i_tx_buffer[0] = i_device_id
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_METADATA

        # Configure TX packet
        self._uniprot.config_tx_packet(2)

        # Configure RX packet
        self._uniprot.config_rx_packet(Bridge.MAX_RX_BUFFER_BYTES)

        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeDeviceNotFound as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeDeviceNotFound(message)

        except BridgeNackFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeNackFail(message)

        except BridgeDeviceRxBufferOverflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeDeviceRxBufferOverflow(message)

        except BridgeResetFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_metadata_from_device]" + message)
            raise BridgeResetFail(message)

        # Test if received Device ID is same
        if i_rx_buffer[0] != i_device_id:
            # This should not happen.
            message = " Got different Device ID (" + str(i_rx_buffer[0]) + \
                      "), but expected " + str(
                i_device_id) + " . This is failure of" \
                               "communication protocol."
            logger.warn("[get_metadata_from_device]" + message)
            raise BridgeError(message)

        # Test return code - never should happen, but...
        if i_rx_buffer[1] != 0:
            # This never happen. Only one thing that may fail is wrong Device
            # ID, but this is checked before request is send. It can fail only
            # when whole protocol fail -> developer should fix this
            message = "Device returned code: " \
                      + ResCodes.code_to_string(i_rx_buffer[1]) + \
                      " This should not happen. It is seems that there is" \
                      " some problem when transmitting or receiving data."
            logger.critical("[get_metadata_from_device]"
                            "[Uniprot RX data]"
                            + message)
            raise BridgeError(message)

        # Else all seems to be OK -> fill metadata structure
        rx_metadata = BridgeMetadata()

        # Metadata begin at index 2 (3rd byte)
        i_index = 2

        # Load MAX CMD ID
        rx_metadata.max_cmd_id = (i_rx_buffer[i_index]) << 8
        i_index = i_index + 1
        rx_metadata.max_cmd_id = rx_metadata.max_cmd_id + i_rx_buffer[i_index]
        i_index = i_index + 1

        # Load serial number
        rx_metadata.serial = i_rx_buffer[i_index]
        i_index = i_index + 1

        # Clear descriptor
        rx_metadata.descriptor = ""

        # Load descriptor
        while i_rx_buffer[i_index] != 0x00:
            # Add character to descriptor - this is python version dependent
            if sys.version_info[0] == 2:
                rx_metadata.descriptor = rx_metadata.descriptor + \
                                         str(unichr(i_rx_buffer[i_index]))
            elif sys.version_info[0] == 3:
                rx_metadata.descriptor = rx_metadata.descriptor + \
                                         str(chr(i_rx_buffer[i_index]))
            else:
                raise BridgeError("Unsupported python version")

            # Increase index
            i_index = i_index + 1

        # return metadata as object
        return rx_metadata

    # Try to get setting (one) from device
    def get_setting_from_device(self, i_device_id, i_cmd_id):
        from .structs import SettingStruct

        # Check if Device ID is valid
        if i_device_id > self.i_num_of_devices:
            message = " Invalid Device ID. "
            if self.i_num_of_devices < 0:
                message = message + "It looks that bridge was not " \
                                    "initialized. Please call function" \
                                    " Uniprot_init() and check all exceptions"
            else:
                # It look that bridge was initialized, but Device ID is invalid
                message = message + "Maximum Device ID is " + \
                          str(self.i_num_of_devices) + " .\n"

            logger.warn("[get_setting_from_device]" + message)

            raise BridgeError(message)

        if i_device_id < 0:
            logger.warn("[get_setting_from_device]"
                        "Invalid i_Device_ID. Can not be lower than 0")
            raise BridgeError("Invalid i_Device_ID. Can not be lower than 0")

        # Check i_CMD_ID
        if ((i_cmd_id > self.device_metadata[i_device_id].max_cmd_id) or
                (i_cmd_id < 0)):
            message = " Invalid CMD ID (input parameter: " + \
                      str(i_cmd_id) + ").\n Minimum CMD ID is 0. Maximum CMD" \
                                      " ID for device " + \
                      str(i_device_id) + " is " + \
                      str(self.device_metadata[i_device_id].max_cmd_id) + \
                      "\n"

            logger.warn("[get_setting_from_device]" + message)
            raise BridgeError(message)

        if i_cmd_id > 0xFFFF:
            logger.warn("[get_setting_from_device]"
                        " i_CMD_ID is longer than 2B. Protocol send just"
                        " 2 LSB Bytes.\n")
            i_cmd_id = i_cmd_id & 0xFFFF

        # Fill TX buffer by zeros
        i_tx_buffer = [0x00] * 4
        # Device ID
        i_tx_buffer[0] = i_device_id
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_GET_SETTING
        # CMD ID - must be split into two Bytes
        i_tx_buffer[2] = i_cmd_id >> 8
        i_tx_buffer[3] = i_cmd_id & 0xFF

        # Configure TX packet
        self._uniprot.config_tx_packet(4)

        # Configure RX packet
        self._uniprot.config_rx_packet(Bridge.MAX_RX_BUFFER_BYTES)

        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeDeviceNotFound as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeDeviceNotFound(message)

        except BridgeNackFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeNackFail(message)

        except BridgeDeviceRxBufferOverflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeDeviceRxBufferOverflow(message)

        except BridgeResetFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[get_setting_from_device]" + message)
            raise BridgeResetFail(message)

        # Test if received DID is same
        if i_rx_buffer[0] != i_device_id:
            # This should not happen.
            message = " Got different Device ID (" + str(i_rx_buffer[0]) + \
                      "), but expected " + str(
                i_device_id) + " . This is failure of" \
                               "communication protocol.\n"
            logger.error("[get_setting_from_device]"
                         + message)
            raise BridgeError(message)

        # Check return code - should be 0, else there is bug in protocol
        if i_rx_buffer[1] != 0:
            # This never happen. Only one thing that may fail is wrong Device
            # ID, but this is checked before request is send. It can fail only
            # when whole protocol fail -> developer should fix this
            message = " Device returned code: " \
                      + ResCodes.code_to_string(i_rx_buffer[1]) + \
                      ". Please refer to source code what error code means." \
                      " However this should not happen. It is seems that" \
                      " there is some problem when transmitting or receiving" \
                      " data."
            logger.critical("[get_setting_from_device]" + message)
            raise BridgeError(message)

        # Check CMD ID
        if ((i_rx_buffer[2] << 8) + i_rx_buffer[3]) != i_cmd_id:
            message = " Device returned different CMD ID (" + \
                      str((i_rx_buffer[2] << 8) + i_rx_buffer[3]) + \
                      "), but expected " + \
                      str(i_cmd_id) + ". This means failure on protocol layer."
            logger.critical("[get_setting_from_device]" + message)
            raise BridgeError(message)

        # Else all seems to be OK -> fill structure
        rx_config = SettingStruct()

        # Index for rx_buffer - begin at 4
        i_index_rx_buffer = 4

        # Load data to struct (load byte by byte)

        # IN TYPE
        rx_config.in_type = i_rx_buffer[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer + 1

        # IN MIN
        rx_config.in_min = (i_rx_buffer[i_index_rx_buffer] << 24)
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.in_min = (rx_config.in_min +
                            (i_rx_buffer[i_index_rx_buffer] << 16))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.in_min = (rx_config.in_min +
                            (i_rx_buffer[i_index_rx_buffer] << 8))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.in_min = (rx_config.in_min +
                            (i_rx_buffer[i_index_rx_buffer]))
        i_index_rx_buffer = i_index_rx_buffer + 1

        # According to type, retype variable
        rx_config.in_min = self.retype(rx_config.in_min, rx_config.in_type)

        # IN MAX
        rx_config.in_max = (i_rx_buffer[i_index_rx_buffer] << 24)
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.in_max = (rx_config.in_max +
                            (i_rx_buffer[i_index_rx_buffer] << 16))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.in_max = (rx_config.in_max +
                            (i_rx_buffer[i_index_rx_buffer] << 8))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.in_max = (rx_config.in_max +
                            (i_rx_buffer[i_index_rx_buffer]))
        i_index_rx_buffer = i_index_rx_buffer + 1

        # According to type, retype variable
        rx_config.in_max = self.retype(rx_config.in_max, rx_config.in_type)

        # OUT TYPE
        rx_config.out_type = i_rx_buffer[i_index_rx_buffer]
        i_index_rx_buffer = i_index_rx_buffer + 1

        # OUT MIN
        rx_config.out_min = (i_rx_buffer[i_index_rx_buffer] << 24)
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_min = (rx_config.out_min +
                             (i_rx_buffer[i_index_rx_buffer] << 16))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_min = (rx_config.out_min +
                             (i_rx_buffer[i_index_rx_buffer] << 8))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_min = (rx_config.out_min +
                             (i_rx_buffer[i_index_rx_buffer]))
        i_index_rx_buffer = i_index_rx_buffer + 1

        # According to type, retype variable
        rx_config.out_min = self.retype(rx_config.out_min, rx_config.out_type)

        # OUT MAX
        rx_config.out_max = (i_rx_buffer[i_index_rx_buffer] << 24)
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_max = (rx_config.out_max +
                             (i_rx_buffer[i_index_rx_buffer] << 16))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_max = (rx_config.out_max +
                             (i_rx_buffer[i_index_rx_buffer] << 8))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_max = (rx_config.out_max +
                             i_rx_buffer[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer + 1
        # According to type, retype variable
        rx_config.out_max = self.retype(rx_config.out_max, rx_config.out_type)

        # OUT VALUE
        rx_config.out_value = (i_rx_buffer[i_index_rx_buffer] << 24)
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_value = (rx_config.out_value +
                               (i_rx_buffer[i_index_rx_buffer] << 16))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_value = (rx_config.out_value +
                               (i_rx_buffer[i_index_rx_buffer] << 8))
        i_index_rx_buffer = i_index_rx_buffer + 1
        rx_config.out_value = (rx_config.out_value +
                               i_rx_buffer[i_index_rx_buffer])
        i_index_rx_buffer = i_index_rx_buffer + 1
        # According to type, retype variable
        rx_config.out_value = self.retype(rx_config.out_value,
                                          rx_config.out_type)

        # Get name
        while i_rx_buffer[i_index_rx_buffer] != 0x00:
            # This is python version depend (unichr vs chr)
            if sys.version_info[0] == 2:
                rx_config.name = rx_config.name + \
                                 str(unichr(i_rx_buffer[i_index_rx_buffer]))

            elif sys.version_info[0] == 3:
                rx_config.name = rx_config.name + \
                                 str(chr(i_rx_buffer[i_index_rx_buffer]))
            else:
                raise BridgeError("Unsupported python version")
            i_index_rx_buffer = i_index_rx_buffer + 1

        # move to next character (add 1)
        i_index_rx_buffer = i_index_rx_buffer + 1

        # And get descriptor - do not know length
        while i_rx_buffer[i_index_rx_buffer] != 0x00:
            # Add character to string
            if sys.version_info[0] == 2:
                rx_config.descriptor = rx_config.descriptor + \
                                       str(unichr(
                                           i_rx_buffer[i_index_rx_buffer]))
            elif sys.version_info[0] == 3:
                rx_config.descriptor = rx_config.descriptor + \
                                       str(chr(i_rx_buffer[i_index_rx_buffer]))
            else:
                raise BridgeError("Unsupported python version")
            i_index_rx_buffer = i_index_rx_buffer + 1

        return rx_config

    def set_setting_to_device(self, i_device_id, i_cmd_id, i_value=0):
        """ Try to set setting and if success try to read and update actual
            value using get setting.

        :param i_device_id:
        :param i_cmd_id:
        :param i_value:
        :return:
        """
        # Check Device ID
        if i_device_id > self.i_num_of_devices:
            message = " Invalid Device ID. "
            if self.i_num_of_devices < 0:
                message = message + "It looks that bridge was not" \
                                    " initialized. Please call function" \
                                    " Uniprot_init() and check all exceptions"
            else:
                # It looks that bridge was initialized, but device ID is invalid
                message = message + "Maximum Device ID is " + \
                          str(self.i_num_of_devices) + " .\n"
            logger.warn("[set_setting_to_device]" + message)

            raise BridgeError(message)

        if i_device_id < 0:
            message = "Invalid i_Device_ID. Can not be lower than 0"
            logger.warn("[set_setting_from_device]"
                        + message)
            raise BridgeError(message)

        # Now check CMD ID
        if ((i_cmd_id > self.s_metadata[i_device_id].max_cmd_id) or
                (i_cmd_id < 0)):
            message = "Invalid CMD ID. Can not be lower than 0 and higher" \
                      " then " + str(self.s_metadata[i_device_id].max_cmd_id) \
                      + " for device " + str(i_device_id) + " .\n"
            logger.warn("[set_setting_from_device]"
                        + message)
            raise BridgeError(message)
        if i_cmd_id > 0xFFFF:
            logger.warn("[set_setting_to_device]"
                        " i_CMD_ID is longer than 2B. Protocol send just"
                        " 2 LSB Bytes.\n")
            i_cmd_id = i_cmd_id & 0xFFFF

        # According to data type convert data
        data_type = self.s_settings_in_RAM[i_device_id][i_cmd_id].in_type

        # GROUP TYPE
        if data_type == DataTypes.GROUP:
            # Well, this should not happen. To group we should not send
            #  any data.
            # OK, so for now just we will ignore value and just send warning to
            # log, because it is not big deal. Maybe in new version will be
            # device capable receive group messages.
            logger.warn("[set_setting_to_device] You are trying send data to"
                        "data type group!\n It is not forbidden, "
                        "however in this"
                        "version it is not recommended!\n Please double check"
                        "firmware version. Or maybe it is just bug.")

        # VOID TYPE
        # Better than mess transmit zeros
        elif data_type == DataTypes.VOID:
            i_value = 0

        # CHAR TYPE
        elif data_type == DataTypes.CHAR:
            # If char type recalculate to number - this is pretty easy
            # TODO: Check this, I think it's not going to work
            i_value = ord(i_value[0])

        # FLOAT TYPE
        elif data_type == DataTypes.FLOAT:
            i_value = struct.pack("f", i_value)
            i_value = bytearray(i_value)
            i_value = (i_value[3] << 24) + (i_value[2] << 16) + \
                      (i_value[1] << 8) + (i_value[0])

        # UINT* TYPES
        elif data_type in (DataTypes.UINT,
                           DataTypes.UINT8,
                           DataTypes.UINT16,
                           DataTypes.UINT32):

            # Check sign
            if i_value < 0:
                # Well, value should be unsigned. In the end it really does not
                # matter, but it could be a mistake somewhere.
                # At least log warning
                logger.warn("[set_setting_to_device] Value is negative, but it "
                            "should be only positive (because data type is"
                            " unsinged). Value will be transmitted, "
                            "but in device will be used as unsigned!\n")

        # INT and UINT TYPES
        else:
            msg_wide_variable = "[set_setting_to_device] Value is wider" + \
                                " than maximum. Application send only low "

            # Note that int and uint should be 32 bit long.
            if data_type in (DataTypes.UINT32,
                             DataTypes.INT32,
                             DataTypes.UINT,
                             DataTypes.INT):

                if i_value > 0xFFFFFFFF:
                    i_value = i_value & 0xFFFFFFFF
                    logger.warn(msg_wide_variable + "4 Bytes")

            # Check number size (16b)
            elif data_type in (DataTypes.UINT16, DataTypes.INT16):
                if i_value > 0xFFFF:
                    i_value = i_value & 0xFFFF
                    logger.warn(msg_wide_variable + "2 Bytes")

            # Check number size (8b)
            elif data_type in (DataTypes.UINT8, DataTypes.INT8):

                if i_value > 0xFF:
                    i_value = i_value & 0xFF
                    logger.warn(msg_wide_variable + "1 Byte")
            else:
                # This should not happen, because if does, that means, that
                # we forget some int/uint options
                msg = "[set_setting_to_device] Programmer forget test some " + \
                      "int or uint data type. You must correct problem in " + \
                      "code :/ This never should happen."
                logger.critical(msg)

        logger.debug("[set_setting_to_device] Value to send: {0}".format(
            i_value))

        # Fill TX buffer by zeros
        i_tx_buffer = [0x00] * 8
        # Device ID
        i_tx_buffer[0] = i_device_id
        # Bridge command (request ID)
        i_tx_buffer[1] = Bridge.STATE_REQUEST_SET_SETTING
        # CMD ID - must be split into two Bytes
        i_tx_buffer[2] = (i_cmd_id >> 8)
        i_tx_buffer[3] = i_cmd_id & 0xFF
        # i_value - 4B - split
        i_tx_buffer[4] = (i_value >> 24) & 0xFF
        i_tx_buffer[5] = (i_value >> 16) & 0xFF
        i_tx_buffer[6] = (i_value >> 8) & 0xFF
        i_tx_buffer[7] = i_value & 0xFF

        # Configure TX packet
        self._uniprot.config_tx_packet(8)

        # Configure RX packet
        self._uniprot.config_rx_packet(Bridge.MAX_RX_BUFFER_BYTES)

        try:
            i_rx_buffer = self.send_request_get_data(i_tx_buffer)
        except BridgeDeviceNotFound as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeDeviceNotFound(message)

        except BridgeNackFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeNackFail(message)

        except BridgeDeviceRxBufferOverflow as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeDeviceRxBufferOverflow(message)

        except BridgeResetFail as e:
            message = "[send_request_get_data]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeResetFail(message)

        # Test if received DID is same
        if i_rx_buffer[0] != i_device_id:
            # This should not happen.
            message = " Got different Device ID (" + str(i_rx_buffer[0]) + \
                      "), but expected " + str(
                i_device_id) + " . This is failure of" \
                               "communication protocol.\n"
            logger.error("[set_setting_to_device]"
                         + message)
            raise BridgeError(message)

        # Check return code - should be 0, however it cant't
        if i_rx_buffer[1] != 0:
            dev_code = ResCodes.code_to_string(i_rx_buffer[1])
            message = (" Device returned code: {0}\n"
                       "  Driver: {1}  (Device ID: {2})\n"
                       "  CMD: {3}  (CMD ID: {4})\n".format(
                        dev_code, self.s_metadata[i_device_id].descriptor,
                        i_device_id,
                        self.s_settings_in_RAM[i_device_id][i_cmd_id].name,
                        i_cmd_id))
            logger.warning("[set_setting_to_device]" + message)
            raise BridgeError(message)

        # Setting was set, but program should update value -> call
        # get_setting_from_device and update data in RAM
        try:
            self.s_settings_in_RAM[i_device_id][i_cmd_id] = \
                self.get_setting_from_device(i_device_id, i_cmd_id)
        except BridgeDeviceNotFound as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeDeviceNotFound(message)

        except BridgeNackFail as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeNackFail(message)

        except BridgeDeviceRxBufferOverflow as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeDeviceRxBufferOverflow(message)

        except BridgeResetFail as e:
            message = "[get_setting_from_device]" + str(e)
            logger.error("[set_setting_to_device]" + message)
            raise BridgeResetFail(message)

        # If no exception occurred -> return result code as text
        return ResCodes.code_to_string(i_rx_buffer[1])

    @property
    def device_metadata(self):
        """ Metadata of all devices as variable
        """
        return self.s_metadata

    def get_max_device_id(self):
        """ Return maximum Device_ID, which can be used
            as max index for metadata.

        :return:
        """
        return self.i_num_of_devices

    @property
    def all_settings(self):
        """ Return complex device settings as one object
        :return:
        """
        return self.s_settings_in_RAM
