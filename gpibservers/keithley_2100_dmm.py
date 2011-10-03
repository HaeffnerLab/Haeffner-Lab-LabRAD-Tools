# Copyright (C) 2011 Dylan Gorman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
### BEGIN NODE INFO
[info]
name = Keithley Server
version = 1.0
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import setting
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

class KeithleyWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.dcVolts = yield self.getdcVolts()
        self.outputStateKnown = False
        self.output = True

    @inlineCallbacks
    def getdcVolts(self):
        self.dcVolts = yield self.query('MEAS:VOLT:DC?').addCallback(float)
        returnValue(self.dcVolts)

class KeithleyServer(GPIBManagedServer):
    name = 'Keithley 2100 DMM' # Server name
    deviceName = 'KEITHLEY INSTRUMENTS INC. MODEL 2100' # Model string returned from *IDN?
    deviceWrapper = KeithleyWrapper

    @setting(10, 'DC Voltage')
    def dcVolts(self, c):
        dev = self.selectedDevice(c)
        return dev.dcVolts

    @setting(11, 'Get DC Volts', returns = 'v')
    def getdcVolts(self, c):
        dev = self.selectedDevice(c)
        voltage = yield dev.getdcVolts()
        returnValue(voltage)
        
__server__ = KeithleyServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
