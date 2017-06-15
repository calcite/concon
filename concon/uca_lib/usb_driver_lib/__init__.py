import os

if os.name == "posix":
    from .linux import *
elif os.name == "nt":
    from .windows import *
else:
    raise Exception("Unsupported OS")
