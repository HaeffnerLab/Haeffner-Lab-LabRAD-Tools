from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue
from twisted.internet.threads import deferToThread
from ctypes import c_long, c_buffer, c_float, windll, pointer

"""
### BEGIN NODE INFO
[info]
name =  Picomotor Server
version = 1.1
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

class Picomotor():
    def __init__(self):
        self.dll = windll.LoadLibrary("APT.dll")
        #self.aptdll.EnableEventDlg(False)
        self.dll.APTInit()