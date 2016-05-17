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


#mod. B Timar 2015-07-10
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
from labrad.units import WithUnit


class KeithleyWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.voltage = yield self.getvoltage()
        self.current = yield self.getcurrent()
        self.outputStateKnown = False
        self.output = True

    @inlineCallbacks
    def getvoltage(self):
        """return the voltage output/limit in volts"""
        self.voltage = yield self.query('SOURCE:VOLT?').addCallback(float)
        
        returnValue(self.voltage)

    @inlineCallbacks
    def getcurrent(self):
        """return the current output/limit, in amps"""
        self.current = yield self.query('SOURCE:CURR?').addCallback(float)
        
        returnValue(self.current)
        
    @inlineCallbacks
    def setvoltage(self, v):
        """set a new voltage output or limit"""
        
        yield self.write('SOURCE:VOLT {0}'.format(v))

    @inlineCallbacks
    def setcurrent(self, i):
        """set a new current output or limit"""
        yield self.write('SOURCE:CURR {0}'.format(i))
        
        

class KeithleyServer(GPIBManagedServer):
    name = 'Keithley 2220-30-1' # Server name
    deviceName = 'Keithley instruments 2220-30-1' #string returned from *IDN?, withot the version number or serial no, no commas.
    deviceWrapper = KeithleyWrapper

    @setting(10, 'Voltage', volts='v', returns = 'v')
    def voltage(self, c, volts=None):
        """get or set the power supply voltage output/limit.
            the value will be returned either way. Type: float (volts)"""
        dev = self.selectedDevice(c)
        if (volts is None):
            volts = yield dev.getvoltage()
        else:
            yield dev.setvoltage(volts)
        
        returnValue(volts)
    
    @setting(20, 'Current', amps='v', returns = 'v')
    def current(self, c, amps=None):
        """get or set the power supply current output/limit. the value will
        be returned either way. Type: float (amps)"""
        
        dev = self.selectedDevice(c)
        if (amps is None):
            amps = yield dev.getcurrent()
        else:
            #send setcurrent a float, not a Value -- otherwise
            #labrad has trouble figuring
            yield dev.setcurrent(amps)
        
        returnValue(amps)
        
__server__ = KeithleyServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
