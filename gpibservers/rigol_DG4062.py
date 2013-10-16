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
name = Rigol DG4062 Server
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
from labrad.units import WithUnit

class RigolDG4062Wrapper(GPIBDeviceWrapper):
    
    @inlineCallbacks
    def initialize(self):
        self.frequency = yield self.getFrequency()

    @inlineCallbacks
    def getFrequency(self):
        frequency = yield self.query('SOURce1:FREQuency?\n').addCallback(float)
        self.frequency = WithUnit(frequency, 'Hz')
        returnValue(self.frequency)
    
    @inlineCallbacks
    def setFrequency(self, f):
        if self.frequency != f:
            yield self.write('SOURce1:FREQuency:FIXed {0}\n'.format(f['Hz']))
            self.frequency = f

 
class RigolDG4062Server(GPIBManagedServer):
    """Provides basic CW control for Agilent Signal Generators"""
    name = 'Rigol DG4062 Server'
    deviceName = 'Rigol Technologies DG4062'
    deviceWrapper = RigolDG4062Wrapper

    @setting(10, 'Frequency', f=['v[MHz]'], returns=['v[MHz]'])
    def frequency(self, c, f=None):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if f is not None:
            yield dev.setFrequency(f)
        returnValue(dev.frequency)

__server__ = RigolDG4062Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
