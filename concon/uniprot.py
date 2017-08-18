"""
  .. module: concon.uniprot
  .. synopsis: Universal protocol designed for 8 bit embedded systems

    Slowly remove print_if_debug and replace by logger (logging)

    Functions for higher layer:
    Uniprot_init() - must be called first
    Uniprot_close() - should be called when no communication is needed
                   (at the end of program)

    Uniprot_USB_rx_data() - when want RX data
    Uniprot_USB_tx_data( i_tx_data ) - when want TX data
"""

import logging.config
from crc16_xmodem import *
from usb_driver import UsbDriver, UsbDevice

logger = logging.getLogger('Uniprot <---> USB')


class UniprotException(Exception):
    pass


class UniprotExceptionResetSuccess(UniprotException):
    pass


class UniprotExceptionDeviceNotFound(UniprotException):
    pass


class UniprotExceptionNackFail(UniprotException):
    pass


class UniprotExceptionRxBufferOverflow(UniprotException):
    pass


class UniPacketConfig(object):
    """Static structure for packet configuration"""

    def __init__(self):
        self.i_rx_num_of_data_bytes = 0
        self.i_rx_max_num_of_data_bytes = 0
        self.i_rx_config_done = False
        self.i_tx_num_of_data_bytes = 0
        self.i_tx_config_done = False


class UniStatus(object):
    """Static structure for status (error codes and flags)"""

    def __init__(self):
        self.uni_sr_error_flag_tx_not_configured = False
        self.uni_sr_error_flag_rx_not_configured = False
        self.uni_sr_waiting_for_ack = False
        self.uni_sr_sending_ack = False
        self.uni_sr_error_flag_header_rx = False
        self.uni_sr_error_flag_crc_rx = False
        self.uni_sr_error_flag_tail_rx = False
        self.uni_sr_error_flag_general_rx = False
        self.uni_sr_error_flag_general_tx = False
        self.uni_sr_error_flag_overflow_rx = False
        self.uni_sr_flag_rx_done = False
        self.uni_sr_flag_tx_done = False


class Uniprot(object):

    UNI_MAX_NACK_RETRY_COUNT = 10

    UNI_RES_CODE_CRC_ERROR = "CRC ERROR"

    UNI_RES_CODE_ACK = "ACK"

    UNI_RES_CODE_ACK_WARNING = "ACK Warning: number of data bytes > max!"

    UNI_RES_CODE_NACK = "NACK"

    UNI_RES_CODE_RX_BUFFER_OVERFLOW = "RX BUFFER OVERFLOW"

    UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW = "DEVICE BUFFER OVERFLOW"

    UNI_RES_CODE_RESET = "RESET"

    UNI_RES_CODE_UNKNOWN_COMMAND = "FATAL ERROR! UNKNOWN COMMAND. " \
                                   "Different protocol version?"

    UNI_RES_CODE_SUCCESS = "Yes, all OK!"

    UNI_RES_CODE_DEVICE_NOT_FOUND = "Device not found. " \
                                    "Please make sure that device is connected"

    UNI_CHAR_HEADER = ord('H')

    UNI_CHAR_DATA = ord('D')

    UNI_CHAR_TAIL = ord('T')

    UNI_CHAR_ACK = ord('A')

    UNI_CHAR_NACK = ord('N')

    UNI_CHAR_RESET = ord('R')

    UNI_CHAR_BUFFER_OVERFLOW = ord('O')

    def __init__(self, vid, pid, timeout=UsbDriver.USB_TIMEOUT_MS):
        """Connect to the target device if possible"""
        self._usb_vid = vid
        self._usb_pid = pid
        self._timeout = timeout
        self._device = UsbDevice('NA', vid, pid, None)
        res = self._device.open(timeout=timeout)

        if res == 404:
            raise UniprotExceptionDeviceNotFound(" Device not found!\n")

        if res == -1:
            raise UniprotException(" RX buffer has invalid size!\n")

        self._packet_config = UniPacketConfig()
        self._status = UniStatus()
        self._i_buffer_rx = None

    def close(self):
        """Disconnect from the target device if possible."""

        status = self._device.close()

        if status != 0:
            raise UniprotExceptionDeviceNotFound(" Device not found!\n")

    def config_tx_packet(self, i_tx_num_of_data_bytes):
        """ Configure TX packet - define data frame size.

        :param i_tx_num_of_data_bytes: Number of data Bytes
        """

        self._packet_config.i_tx_num_of_data_bytes = i_tx_num_of_data_bytes

        self._packet_config.i_tx_config_done = True

        # Test if there is any problem with TX device
        if not self._status.uni_sr_error_flag_general_tx:
            # If there is not any problem -> set TX_done flag
            self._status.uni_sr_flag_tx_done = True

    def config_rx_packet(self, i_rx_max_num_of_data_bytes):
        """ Configure RX packet - define data frame size.

        :param i_rx_max_num_of_data_bytes:
        """

        self._packet_config.i_rx_max_num_of_data_bytes = \
            i_rx_max_num_of_data_bytes

        self._packet_config.i_rx_config_done = True

    @classmethod
    def process_rx_status_data(cls, buffer_rx):
        """ Process received status data (ACK, NACK,....)

            This process read status data (usually 3B)
            and do necessary processing.

        :param buffer_rx:  Received data.
        :return: Result code
        """

        # Set CRC to zero
        crc16 = 0

        # Test CRC first
        crc16 = crc_xmodem_update(crc16, buffer_rx[0])
        crc16 = crc_xmodem_update(crc16, buffer_rx[1])
        crc16 = crc_xmodem_update(crc16, buffer_rx[2])
        logger.debug(
            "[Uni_process_rx_status_data] CRC result: " + str(crc16) + "\n\n")

        if crc16 != 0:
            return cls.UNI_RES_CODE_CRC_ERROR

        # Test for ACK
        if buffer_rx[0] == cls.UNI_CHAR_ACK:
            return cls.UNI_RES_CODE_ACK

        # Test for NACK
        if buffer_rx[0] == cls.UNI_CHAR_NACK:
            return cls.UNI_RES_CODE_NACK

        # Test for RESET
        if buffer_rx[0] == cls.UNI_CHAR_RESET:
            return cls.UNI_RES_CODE_RESET

        # test for Buffer overflow from device
        if buffer_rx[0] == cls.UNI_CHAR_BUFFER_OVERFLOW:
            return cls.UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW

        # If no status defined -> FAIL
        return cls.UNI_RES_CODE_UNKNOWN_COMMAND

    def usb_tx_command(self, command_char):
        """ Send command over USB.

        :param command_char: Command character (Example: const_UNI_CHAR_ACK)
        """

        # Initialize crc16 value
        crc16 = 0

        # Fill buffer by zeros
        i_buffer_tx = [0x00] * 8

        i_buffer_tx[0] = command_char

        # Calculate CRC
        crc16 = crc_xmodem_update(crc16, command_char)

        # And load crc16 value to TX buffer

        # CRC16 - MSB
        i_buffer_tx[1] = (crc16 >> 8) & 0xFF

        # CRC16 - LSB
        i_buffer_tx[2] = crc16 & 0xFF

        # Check if command is reset
        if command_char == self.UNI_CHAR_RESET:
            # Add reset symbols (Emergency reset from host)
            i_buffer_tx[3] = self.UNI_CHAR_RESET
            i_buffer_tx[4] = self.UNI_CHAR_RESET
            i_buffer_tx[5] = self.UNI_CHAR_RESET
            i_buffer_tx[6] = self.UNI_CHAR_RESET
            i_buffer_tx[7] = self.UNI_CHAR_RESET

        # Check if not ACK -> else probably error -> clear input buffers
        if command_char != self.UNI_CHAR_ACK:
            # Clear input buffer (just for case)
            self.usb_clear_rx_buffer(3)

        # Buffer is ready, send data
        self._device.tx_data(i_buffer_tx)

    def usb_try_tx_data(self, i_tx_data):
        """ Try send data and return command code (ACK, NACK and so on).

        :param i_tx_data:  Data (array) witch will be send.
        :return: Status code.
        """

        # Temporary buffer for TX data (8 Bytes)
        i_buffer_tx = [0x00] * 8

        # Temporary buffer for RX data (8 Bytes)
        self._i_buffer_rx = [0x00] * 8

        # CRC variable
        i_crc16 = 0

        # Index for i_tx_data
        i_tx_data_index = 0

        # Load header to TX buffer
        # Header character
        i_buffer_tx[0] = self.UNI_CHAR_HEADER
        i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[0])
        # Number of data Bytes - H
        i_buffer_tx[1] = ((self._packet_config.i_tx_num_of_data_bytes >> 8)
                          & 0xFF)
        i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[1])
        # Number of data Bytes - L
        i_buffer_tx[2] = self._packet_config.i_tx_num_of_data_bytes & 0xFF
        i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[2])
        # Data character
        i_buffer_tx[3] = self.UNI_CHAR_DATA
        i_crc16 = crc_xmodem_update(i_crc16, i_buffer_tx[3])

        # Now calculate remaining data Bytes + Tail + CRC16
        i_tx_remain_data_bytes = self._packet_config.i_tx_num_of_data_bytes + 3
        # There is +3 because in real we must send tail plus CRC -> 3 Bytes

        i_buffer_tx_index = 4

        # Send all remaining bytes
        while i_tx_remain_data_bytes >= 1:

            # Fill buffer_tx until is full or until i_tx_remain_data_bytes >= 1
            while (i_tx_remain_data_bytes >= 1) and (i_buffer_tx_index < 8):

                # Test if there are data - must remain more than 3 Bytes
                if i_tx_remain_data_bytes >= 4:
                    # Data - load them to the buffer_tx
                    i_buffer_tx[i_buffer_tx_index] = i_tx_data[i_tx_data_index]
                    # Calculate CRC
                    i_crc16 = crc_xmodem_update(i_crc16,
                                                i_buffer_tx[i_buffer_tx_index])
                    # Increase index
                    i_tx_data_index = i_tx_data_index + 1

                # Test if there is tail
                elif i_tx_remain_data_bytes == 3:
                    # Add tail do TX buffer
                    i_buffer_tx[i_buffer_tx_index] = self.UNI_CHAR_TAIL
                    # Calculate CRC
                    i_crc16 = \
                        crc_xmodem_update(i_crc16,
                                          i_buffer_tx[i_buffer_tx_index])

                # Test if there is CRC High Byte
                elif i_tx_remain_data_bytes == 2:
                    # Add CRC H to buffer
                    i_buffer_tx[i_buffer_tx_index] = (i_crc16 >> 8) & 0xFF

                # Last option - CRC Low byte
                else:
                    # Add CRC L to buffer
                    i_buffer_tx[i_buffer_tx_index] = i_crc16 & 0xFF

                # Increase index
                i_buffer_tx_index = i_buffer_tx_index + 1
                # Decrease i_remain_data_Bytes
                i_tx_remain_data_bytes = i_tx_remain_data_bytes - 1

            # If buffer i_buffer_tx is full, then send data over USB
            # and reset i_buffer_tx_index. However, if program
            # should send last byte (if condition) then is need to call
            # a different function and check ACK/NACK command

            if i_tx_remain_data_bytes <= 0:
                # Send last bytes
                self._device.tx_data(i_buffer_tx)
                # Get command
                self._i_buffer_rx = self._device.rx_data()
                logger.debug("[Uniprot_USB_try_tx_data] Response received:\n" +
                             str(self._i_buffer_rx) + "\n")

                status = self.process_rx_status_data(self._i_buffer_rx)

                logger.debug("[Uniprot_USB_try_tx_data] Response status: " +
                             str(status) + "\n")
                # Return command status (ACK, NACK and so on)
                return status
            else:
                # Else just send another packet
                self._device.tx_data(i_buffer_tx)

            # Anyway - clear some variables
            i_buffer_tx_index = 0

            # Load dummy data to buffer
            for i in range(8):
                i_buffer_tx[i] = 0xFF

    def usb_tx_data(self, i_tx_data):
        """ Send data over USB.

        :param i_tx_data:  Data to be send.
        :return:
        """
        try:
            status = self.usb_try_tx_data(i_tx_data)
        except:
            message = "[Try TX data] Device not found!\n"
            logger.error("[Uniprot_USB_tx_data]" + message)
            raise UniprotExceptionDeviceNotFound(message)

        # Counter for NACK command. If reach limit -> raise exception
        i_nack_cnt = self.UNI_MAX_NACK_RETRY_COUNT

        # Send data again if there is NACK or CRC ERROR
        while (status == self.UNI_RES_CODE_NACK) or \
                (status == self.UNI_RES_CODE_CRC_ERROR):

            # RX all data and throw them - clean buffers
            logger.debug("[Uniprot_USB_tx_data] Throwing data....\n")
            self.usb_clear_rx_buffer()

            # Confirm, that all data was received (send ACK)
            try:
                self.usb_tx_command(self.UNI_CHAR_ACK)
            except:
                raise UniprotExceptionDeviceNotFound(
                    "[Try TX cmd] Device not found! (loop)\n")

            logger.warn("[Uniprot_USB_tx_data]"
                        " NACK or CRC error. TX data again... (" +
                        str(self.UNI_MAX_NACK_RETRY_COUNT - i_nack_cnt) +
                        ").")

            try:
                status = self.usb_try_tx_data(i_tx_data)
            except:
                raise UniprotExceptionDeviceNotFound(
                    "[Try TX data] Device not found! (loop)\n")

            i_nack_cnt = i_nack_cnt - 1
            if i_nack_cnt == 0:
                logger.error("[Uniprot_USB_tx_data]"
                             " Retry count reach limit! (loop)\n")
                raise UniprotExceptionNackFail(
                    " NACK retry count reach limit!\n")

        # Test for other options

        # Test for ACK (standard behaviour)
        if status == self.UNI_RES_CODE_ACK:
            return self.UNI_RES_CODE_SUCCESS

        # Test Exceptions

        # Test for buffer overflow on device -> higher layer should solve this
        if status == self.UNI_RES_CODE_DEVICE_BUFFER_OVERFLOW:
            # EXCEPTION
            message = " Device RX buffer overflow" \
                      "It looks like device is out of RAM." \
                      "Program can not send even 2Bytes. " \
                      "This is fatal problem and can" \
                      "not be solved by this program. Sorry :(\n"
            logger.critical("[Uniprot_USB_tx_data]" + message)
            raise UniprotExceptionRxBufferOverflow(message)

        # Test for restart or unknown command

        if (status == self.UNI_RES_CODE_RESET) or \
                (status == self.UNI_RES_CODE_UNKNOWN_COMMAND):
            # Restart device

            # Try close device
            try:
                self.close()
            except:
                # Just dummy operation - not fail
                pass
            # If device not found - nevermind

            # Try initialize device again
            try:
                self._device.open(timeout=self._timeout)
            except UniprotExceptionDeviceNotFound as e:
                # If reinitialization failed
                # EXCEPTION
                message = "[Re-init failed]" + str(e)
                logger.error("[Uniprot_USB_tx_data]" + message)
                raise UniprotExceptionDeviceNotFound(message)

            # Else reinitialization OK

            # Anyway this is not a standard behaviour - higher layer should
            # send all data again
            # EXCEPTION
            message = " Restart occurred!\n"
            logger.warn("[Uniprot_USB_tx_data]" + message)
            raise UniprotExceptionResetSuccess(message)

        # Program never should get to this point (critical error)
        message = "[Uniprot_USB_tx_data] Internal error. Unexpected status :(" \
                  " Exiting...\n"
        logger.critical(message)
        raise UniprotException(message)

    def usb_try_rx_data(self):
        """ Try receive data and return command code (ACK, NACK and so on).

        :return:
        """

        # Temporary buffer for TX data (8 Bytes)
        # i_buffer_tx = [0x00] * 8

        # Temporary buffer for RX data
        # i_buffer_rx_8 = [0x00] * 8
        # Index for i_buffer_rx_8 - data begin at index 4 (index 0-3 is header)
        i_buffer_rx_8_index = 4

        # Index for i_buffer_rx (user data)
        i_buffer_rx_index = 0

        # Set CRC to zero
        crc16 = 0

        # Warning if there is some catch
        i_warning = 0

        # RX first frame
        logger.debug("[Uniprot_USB_try_rx_data] Before USB driver RX")
        i_buffer_rx_8 = self._device.rx_data()

        logger.debug("[Uniprot_USB_try_rx_data] RAW uniprot data (begin):\n" +
                     str(i_buffer_rx_8) + "\n\n\n")

        # Try to find header
        if ((i_buffer_rx_8[0] == self.UNI_CHAR_HEADER) and
                (i_buffer_rx_8[3] == self.UNI_CHAR_DATA)):

            # If header is found save information about number of bytes
            #  (MSB first)
            self._packet_config.i_rx_num_of_data_bytes = \
                (i_buffer_rx_8[1] << 8) + (i_buffer_rx_8[2])
            # Create RX buffer
            # RX buffer for data
            self._i_buffer_rx = ([0x00] *
                                 self._packet_config.i_rx_num_of_data_bytes)

            # Test if received number of bytes is higher
            # than user defined maximum.
            # If yes, from PC side it is not a problem (there is enough memory),
            # however program should return at least some kind of warning
            if self._packet_config.i_rx_num_of_data_bytes > \
                    self._packet_config.i_rx_max_num_of_data_bytes:
                i_warning = 1

            # Calculate CRC
            crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[0])
            crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[1])
            crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[2])
            crc16 = crc_xmodem_update(crc16, i_buffer_rx_8[3])
        else:
            # If correct header is not found, return NACK
            logger.debug("[Uniprot_USB_try_rx_data]"
                         " Header not found. NACK\n"
                         + str(self._i_buffer_rx))

            return self.UNI_RES_CODE_NACK

        # Calculate number of Bytes (include tail and CRC16 -> 3B -> +3)
        i_rx_remain_data_bytes = self._packet_config.i_rx_num_of_data_bytes + 3

        # Now save payload (data). RX all remaining bytes
        while i_rx_remain_data_bytes >= 1:

            # Process rest of data received by USB
            while (i_buffer_rx_8_index < 8) and (i_rx_remain_data_bytes >= 1):
                # If there are data
                if i_rx_remain_data_bytes >= 4:
                    self._i_buffer_rx[i_buffer_rx_index] = \
                        i_buffer_rx_8[i_buffer_rx_8_index]
                    # Do CRC calculation
                    crc16 = crc_xmodem_update(
                        crc16, i_buffer_rx_8[i_buffer_rx_8_index])
                    # Increase both index
                    i_buffer_rx_index += 1

                # If there is Tail
                elif i_rx_remain_data_bytes == 3:
                    # Check Tail itself
                    if i_buffer_rx_8[i_buffer_rx_8_index] == self.UNI_CHAR_TAIL:
                        # OK, Tail seems to be all right
                        crc16 = crc_xmodem_update(crc16, self.UNI_CHAR_TAIL)
                    else:
                        # Else send NACK
                        logger.debug("[Uniprot_USB_try_rx_data]"
                                     " Tail not found. NACK\n")
                        return self.UNI_RES_CODE_NACK

                # Test CRC - high Byte
                elif i_rx_remain_data_bytes == 2:
                    crc16 = crc_xmodem_update(
                        crc16, i_buffer_rx_8[i_buffer_rx_8_index])
                # Else CRC - low Byte
                else:
                    crc16 = crc_xmodem_update(
                        crc16, i_buffer_rx_8[i_buffer_rx_8_index])
                    # Test if CRC OK or not

                # Anyway, increase i_buffer_rx_8_index and decrease
                # i_rx_remain_data_bytes
                i_buffer_rx_8_index += 1
                i_rx_remain_data_bytes -= 1

            # When jump out of previous loop -> read new data (if any remain)
            if i_rx_remain_data_bytes >= 1:
                # If there are still any data to receive -> get them!
                logger.debug("[Uniprot_USB_try_rx_data] Before USB RX\n")
                i_buffer_rx_8 = self._device.rx_data()

                # Check data if are correct (not higher than 255 -> timeout)
                if i_buffer_rx_8[0] > 255:
                    # Clear buffer
                    self.usb_clear_rx_buffer(3)
                    # log problem
                    logger.warn("[Uniprot_USB_try_rx_data] Data in buffer >255"
                                " (packet time out)")
                    # Return NACK (problem in communication)
                    return self.UNI_RES_CODE_NACK

                logger.debug("[Uniprot_USB_try_rx_data] RAW uniprot data"
                             ":\n" + str(i_buffer_rx_8) + "\n")

            # Reset i_buffer_rx_8_index
            i_buffer_rx_8_index = 0

        if i_warning == 0:
            # If all right -> return ACK -> higher layer should send ACK command
            return self.UNI_RES_CODE_ACK
        else:
            logger.warning("[Uniprot_USB_try_rx_data]"
                           " Received more Bytes than configured.")
            return self.UNI_RES_CODE_ACK_WARNING

    def usb_rx_data(self):
        """ Receive data over USB.

        :return:  Received data as Byte stream.
        """

        try:
            status = self.usb_try_rx_data()
        except:
            raise UniprotExceptionDeviceNotFound("[Try RX data]"
                                                 " Device not found!\n")

        logger.debug("[Uniprot_USB_rx_data]"
                     "Uniprot RX status (1): " + status + "\n RX Data:\n" +
                     str(self._i_buffer_rx) + "\n")

        # Reset counter
        i_nack_cnt = 0

        # Test status
        while (status != self.UNI_RES_CODE_ACK) and \
                (status != self.UNI_RES_CODE_ACK_WARNING):
            # While is not ACK -> something is wrong -> try to do something!

            logger.warn("[Uniprot_USB_rx_data] Uniprot RX status (while): "
                        + status + " NACK counter: " + str(i_nack_cnt) + "\n")

            # Test for NACK -> if NACK send all data again
            if status == self.UNI_RES_CODE_NACK:
                # Increase NACK counter
                i_nack_cnt = i_nack_cnt + 1

                # Test if NACK counter is const_UNI_MAX_NACK_RETRY_COUNT
                if i_nack_cnt > self.UNI_MAX_NACK_RETRY_COUNT:
                    # Probably OUT of sync -> reset
                    # Set status to reset
                    status = self.UNI_RES_CODE_RESET
                    # And jump to begin of cycle
                    continue

                # Send NACK to device
                try:
                    self.usb_tx_command(self.UNI_CHAR_NACK)
                except:
                    raise UniprotExceptionDeviceNotFound(
                        "[TX CMD (loop)] Device not found!\n")

                # And wait for data
                try:
                    status = self.usb_try_rx_data()
                except:
                    raise UniprotExceptionDeviceNotFound(
                        "[Try RX data (loop)] Device not found!\n")

            elif status == self.UNI_RES_CODE_RESET:
                # Try send reset and close device
                try:
                    self.usb_tx_command(self.UNI_CHAR_RESET)
                    self.close()
                except:
                    # Dummy operation
                    pass
                # Try initialize device again
                try:
                    self._device.open(timeout=self._timeout)
                except UniprotExceptionDeviceNotFound as e:
                    # If reinitialization failed
                    # EXCEPTION
                    raise UniprotExceptionDeviceNotFound(
                        "[Re-init (loop)]" + str(e))

                # Else reinitialization OK -> raise exception
                raise UniprotExceptionResetSuccess("Restart occurred! (loop)\n")

        # Print at least warning if needed
        if status == self.UNI_RES_CODE_ACK_WARNING:
            logger.warn(
                "Data successfully received, but number of received Bytes"
                " was higher than defined maximum. However buffer overflow"
                " is not come.")
        # When ACK - previous while never run -> send ACK and return data
        try:
            self.usb_tx_command(self.UNI_CHAR_ACK)
        except:
            raise UniprotExceptionDeviceNotFound(
                "[TX command] Device not found!\n")

        return self._i_buffer_rx

    def usb_clear_rx_buffer(self, num_of_empty_buffers=2):
        """ Clear USB RX buffer.

        :param num_of_empty_buffers:  Define how many times must receive
                                      "timeout" data, before end this function.
        """
        i_pattern_tmp = [0xFF0] * 8
        i_throw_cnt = 0
        while True:
            # Get data
            i_rx_tmp = self._device.rx_data()
            logger.debug("[Uniprot_USB_clear_rx_buffer] Throw data:"
                         + str(i_rx_tmp) + "\n\n")
            # Check if in buffer are dummy data (usually >255)
            if i_pattern_tmp == i_rx_tmp:
                i_throw_cnt = i_throw_cnt + 1
                # If > limit -> break
                if i_throw_cnt >= num_of_empty_buffers:
                    break
