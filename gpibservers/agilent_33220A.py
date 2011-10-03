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
name = Agilent Server
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

class Agilent33220AWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.frequency = yield self.getFrequency()
        self.amplitude = yield self.getAmplitude()
        self.output = yield self.getOutput()

    @inlineCallbacks
    def getFrequency(self):
        frequency = yield self.query('FREQuency?').addCallback(float)
        self.frequency = frequency / 10.**6 #now in MHz
        returnValue(self.frequency)

    @inlineCallbacks
    def getAmplitude(self):
        self.amplitude = yield self.query('Voltage:UNIT DBM\r\n'+'Voltage?').addCallback(float)
        returnValue(self.amplitude)
    
    @inlineCallbacks
    def getOutput(self):
        state = yield self.query('OUTput?').addCallback(float)
        self.state = bool(state)
        returnValue(self.state)
    
    @inlineCallbacks
    def setFrequency(self, f):
        if self.frequency != f:
            yield self.write('FREQuency {}Mhz'.format(float(f)))
            self.frequency = f
    
    @inlineCallbacks
    def setAmplitude(self, a):
        if self.amplitude != a:
            yield self.write('Voltage:UNIT DBM\r\nVoltage {}'.format(float(a)))
            self.amplitude = a

    @inlineCallbacks
    def setOutput(self, out):
        if self.output != out:
            if out == True:
                comstr = 'OUTPut ON'
            else:
                comstr = 'OUTPut OFF'
            yield self.write(comstr)
            self.output = out

#currently not implemented but possible:
#===============================================================================
#    def VoltageReqStr(self):
#        return 'Voltage:UNIT VPP\r\n'+'Voltage?' + '\r\n'
#    
#    # string to set voltage
#    def VoltageSetStr(self,volt):
#        return 'Voltage:UNIT VPP\r\n'+'Voltage ' +str(volt) + '\r\n'
#
#    #string to get current function
#    def FunctionReqStr(self):
#        return 'FUNCtion?\r\n'
#    
#    # string to set function
#    def FunctionSetStr(self,func):
#        if func == 'SINE':
#            comstr = 'FUNCtion ' + 'SIN' + '\r\n'
#        elif func == 'SQUARE':
#            comstr = 'FUNCtion ' + 'SQU' + '\r\n'
#        elif func == 'RAMP':
#            comstr = 'FUNCtion ' + 'RAMP' + '\r\n'
#        elif func == 'PULSE':
#            comstr = 'FUNCtion ' + 'PULSe' + '\r\n'
#        elif func == 'NOISE':
#            comstr = 'FUNCtion ' + 'NOISe' + '\r\n'
#        elif func == 'DC':
#            comstr = 'FUNCtion ' + 'DC' + '\r\n'
#        return comstr       
#===============================================================================
 

class AgilentServer(GPIBManagedServer):
    """Provides basic CW control for Agilent Signal Generators"""
    name = 'Agilent Server'
    deviceName = 'Agilent Technologies 33220A'
    deviceWrapper = Agilent33220AWrapper

    @setting(10, 'Frequency', f=['v[MHz]'], returns=['v[MHz]'])
    def frequency(self, c, f=None):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if f is not None:
            yield dev.setFrequency(f)
        returnValue(dev.frequency)

    @setting(11, 'Amplitude', a=['v[dBm]'], returns=['v[dBm]'])
    def amplitude(self, c, a=None):
        """Get or set the CW amplitude."""
        dev = self.selectedDevice(c)
        if a is not None:
            yield dev.setAmplitude(a)
        returnValue(dev.amplitude)

    @setting(12, 'Output', os=['b'], returns=['b'])
    def output_state(self, c, os=None):
        """Get or set the output status."""
        dev = self.selectedDevice(c)
        if os is not None:
            yield dev.setOutput(os)
        returnValue(dev.output)

__server__ = AgilentServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
