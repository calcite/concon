# -*- coding: utf-8 -*-
"""
.. module:: concon.crc16_xmodem
    :synopsis: CRC XMODEM algorithm used in Uniprot.
.. moduleauthor:: Martin Stejskal <mstejskal@alps.cz>

Same algorithm as used for AVR in library <util/crc16.h>

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


def crc_xmodem_update(crc, data):
    """ Calculate CRC for 1 byte.

    Polynomial: x^16 + x^12 + x^5 + 1 (0x1021)

    Initial value: 0x0

    Example:: python

        crc_xmodem_update( crc, 0x34 )

    :param crc: 16 bit CRC value
    :param data: 8 bit data value
    """
    # crc must not be higher than 16 bits
    crc = 0xFFFF & crc

    # data must not be higher than 8 bits
    data = 0xFF & data

    crc = crc ^ (data << 8)
    for i in range(8):
        if crc & 0x8000:
            crc = (crc << 1) ^ 0x1021
        else:
            crc = crc << 1

    # Return only 16 bits
    return 0xFFFF & crc
