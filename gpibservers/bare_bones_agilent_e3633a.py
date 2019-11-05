'''
### BEGIN NODE INFO
[info]
name = Bare Bones E3663A
version = 1.0
description =
instancename = Bare Bones E3663A
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 9083477
timeout = 20
### END NODE INFO
'''

import visa
from labrad.server import LabradServer, setting

SERVERNAME = "Bare Bones E3663A"
SIGNAlID = 9083477


class BareBonesE3663a(LabradServer):
    name = "BareBonesE3663A"

    def initServer(self):
        pass


    @setting(0, "connect")
    def connect(self, c):
        self.instr = visa.instrument("GPIB::4")
        self.instr.write("SYST:REM")

    @setting(1, "on")
    def on(self, c):
        self.instr.write("SYST:REM")
        self.instr.write("OUTP:STAT ON")
        self.instr.write("DISP:TEXT:CLE")

    @setting(2, "off")
    def off(self, c):
        self.instr.write("OUTP:STAT OFF")
        self.instr.write("DISP:TEXT 'ITS OFF!'")
        self.instr.write("SYST:LOC")

    @setting(3, "get state", returns="s")
    def get_state(self, c):
        state = self.instr.ask("OUTP?")
        if state == 0:
            return "OFF"
        else:
            return "ON"

    @setting(4, "set current", current="v[]")
    def set_current(self, c, current):
        "APPL 8.0, {:.2f}".format(current)
        self.instr.write("APPL 8.0, {}".format(current))

    @setting(5, "get current", returns="v[]")
    def get_current(self, c):
        return float(self.instr.ask("CURR?"))
		
	@setting(6, "disconnect")
	def disconnect(self, c):
		self.instr.write("SYST:LOC")

__server__ = BareBonesE3663a()

if __name__ == "__main__":
    from labrad import util
    util.runServer(__server__)









