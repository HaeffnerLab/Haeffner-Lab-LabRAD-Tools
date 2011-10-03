# Copyright (C) 2007  Matthew Neeley
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = Tektronix Server
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

class TektronixTDS1002BWrapper(GPIBDeviceWrapper):

    @inlineCallbacks
    def measureReadout(self, readout):
        result = yield self.query('MEASurement:MEAS{}:VALue?'.format(readout)).addCallback(float)
        returnValue(result)

class TektronixServer(GPIBManagedServer):
    """Provides basic control for Tektronix 1002B Oscilloscope"""
    name = 'Tektronix Server'
    deviceName = 'TEKTRONIX TDS 1002B'
    deviceWrapper = TektronixTDS1002BWrapper

    @setting(10, 'measure', readout=['w'], returns=['v'])
    def measure(self, c, readout):
        """Gets the measurement result from one of the available readouts"""
        if readout not in range(1,4): raise Exception("Incorrect Readout Number")
        dev = self.selectedDevice(c)
        result  = yield dev.measureReadout(readout)
        returnValue(result)

__server__ = TektronixServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
