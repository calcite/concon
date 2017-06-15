"""
.. module:: usb_driver_lib.device
    :platform: Unix, Windows
    :synopsis: Classes for description of connected devices
.. moduleauthor:: Martin Stejskal

"""


class DeviceStruct:
  """
  Basic structure for every device
  """
  def __init__(self, name, vid, pid):
    self.name = name
    self.vid = vid
    self.pid = pid

  def __str__(self):
    return " Device name: {0}\n VID: {1}\n PID: {2}\n---------------------\n"\
    "".format(self.name, hex(self.vid), hex(self.pid))


