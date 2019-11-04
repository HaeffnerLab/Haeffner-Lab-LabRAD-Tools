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
name = Agilent N5747A Server
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

class AgilentN5747AWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.voltage = yield self.getVoltage()
        self.current = yield self.getCurrent()
        self.output = yield self.getOutput()
        
    @inlineCallbacks
    def getVoltage(self):
        voltage = yield self.query('VOLT?').addCallback(float)
        voltage = WithUnit(voltage,'V')
        returnValue(voltage)
        
    @inlineCallbacks
    def setVoltage(self, voltage):
        yield self.write('VOLT {}'.format(voltage['V']))
        self.voltage = voltage
        
    @inlineCallbacks
    def getCurrent(self):
        current = yield self.query('CURR?').addCallback(float)
        current = WithUnit(current,'A')
        returnValue(current)
    
    @inlineCallbacks
    def setCurrent(self, current):
        yield self.write('CURR {}'.format(current['A']))
        self.current = current
    
    @inlineCallbacks
    def getOutput(self):
        state = yield self.query('OUTPut?').addCallback(int).addCallback(bool)
        returnValue(state)
    
    @inlineCallbacks
    def setOutput(self, output):
        yield self.write('OUTPut {}'.format(int(output)))
        self.output = output

class AgilentServer(GPIBManagedServer):
    """Provides basic CW control for Agilent Signal Generators"""
    name = 'Agilent N5747A'
    deviceName = 'Agilent Technologies N5747A'
    deviceWrapper = AgilentN5747AWrapper

    @setting(10, 'Voltage', voltage=['v[V]'], returns=['v[V]'])
    def voltage(self, c, voltage=None):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if voltage is not None:
            yield dev.setVoltage(voltage)
        returnValue(dev.voltage)

    @setting(11, 'Current', current=['v[A]'], returns=['v[A]'])
    def current(self, c, current=None):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if current is not None:
            yield dev.setCurrent(current)
        returnValue(dev.current)

    @setting(12, 'Output', output=['b'], returns=['b'])
    def output_state(self, c, output=None):
        """Get or set the output status."""
        dev = self.selectedDevice(c)
        if output is not None:
            yield dev.setOutput(output)
        returnValue(dev.output)

__server__ = AgilentServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
