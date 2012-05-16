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
name = Power Meter Server
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

class ThorlabsPM100AWrapper(GPIBDeviceWrapper):
    
    @inlineCallbacks
    def identify(self):
        name = yield self.query('*IDN?')
        returnValue(name)
    
    @inlineCallbacks
    def measure(self):
        power = yield self.query('READ?').addCallback(float)
        returnValue(power)
    
    @inlineCallbacks
    def setAutoRange(self):
        yield self.write('POWER:RANGe:AUTO ON')
    
    @inlineCallbacks
    def setWavelength(self, wave):
        yield self.write('CORRection:WAVelength {}'.format(wave))

class PowerMeterServer(GPIBManagedServer):
    """Provides basic CW control for Agilent Signal Generators"""
    name = 'Power Meter Server'
    deviceName = 'Thorlabs PM100A'
    deviceWrapper = ThorlabsPM100AWrapper

    @setting(10, 'Identify', returns = 's')
    def identify(self, c):
        dev = self.selectedDevice(c)
        name = yield dev.identify()
        returnValue(name)
        
    @setting(11, 'Measure', returns='v[W]')
    def measure(self, c):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        power = yield dev.measure()
        returnValue(power)
    
    @setting(12, 'Auto Range')
    def auto_range(self, c):
        dev = self.selectedDevice(c)
        yield dev.setAutoRange()
    
    @setting(13, 'Set Wavelength', wavelength = 'v')
    def set_wavelength(self, c, wavelength):
        '''sets the wavelength in nm'''
        dev = self.selectedDevice(c)
        yield dev.setWavelength(wavelength)

if __name__ == '__main__':
    from labrad import util
    util.runServer(PowerMeterServer())
