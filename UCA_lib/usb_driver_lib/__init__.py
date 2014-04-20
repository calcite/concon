import os
import sys

if(os.name == "posix"):
  # Linux
  sys.path.append("UCA_lib/usb_driver_lib/linux")
  from usb_driver_Linux import *
elif(os.name == "nt"):
  # Windows
  sys.path.append("UCA_lib/usb_driver_lib/windows")
  from usb_driver_Windows import *
else:
  # Unsupported OS
  raise("Unsupported OS")