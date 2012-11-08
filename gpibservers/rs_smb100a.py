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
name = RohdeSchwarz Server
version = 1.2
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

class RSSMB100AWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def initialize(self):
        self.frequency = yield self.getFrequency()
        self.amplitude = yield self.getAmplitude()
        self.output = yield self.getOutput()
        self.phase = None

    @inlineCallbacks
    def getFrequency(self):
        frequency = yield self.query('SOURce:FREQuency?').addCallback(float)
        self.frequency = frequency / 10.**6 #now in MHz
        returnValue(self.frequency)

    @inlineCallbacks
    def getAmplitude(self):
        self.amplitude = yield self.query('POWer?').addCallback(float)
        returnValue(self.amplitude)
    
    @inlineCallbacks
    def getOutput(self):
        state = yield self.query('OUTput:STATe?').addCallback(float)
        self.state = bool(state)
        returnValue(self.state)
    
    @inlineCallbacks
    def setFrequency(self, f):
        if self.frequency != f:
            yield self.write('SOURce:FREQuency {}MHZ'.format(float(f)))
            self.frequency = f
    
    @inlineCallbacks
    def setAmplitude(self, a):
        if self.amplitude != a:
            yield self.write('POWer {}'.format(float(a)))
            self.amplitude = a

    @inlineCallbacks
    def setOutput(self, out):
        if self.output != out:
            yield self.write('OUTput:STATe {}'.format(int(out)))
            self.output = out
    
    @inlineCallbacks
    def make_new_list(self, inputs, name):
        freqs,powers = zip(*inputs)
        freqString = "SOURce1:LIST:FREQ" + "".join([" {} MHZ,".format(freq) for freq in freqs])
        powerString = "SOURce1:LIST:POW" + "".join([" {}dBm,".format(pwr) for pwr in powers])
        #deleting the last comma
        freqString = freqString[:-1]
        powerString = powerString[:-1]
        yield self.write('SOURce1:LIST:SEL "{}"'.format(name))
        yield self.write(freqString)
        yield self.write(powerString)
    
    @inlineCallbacks
    def activate_list_mode(self, state):
        if state:
            yield self.write("SOURce1:LIST:MODE STEP") #sets the step mode
            yield self.write("SOURce1:LIST:TRIGger:SOURce EXT") #external triggering
            yield self.write("SOURce1:FREQuency:MODE LIST") #activates step mode (output must be on)
        else:
            yield self.write("SOURce1:FREQuency:MODE CW")
    
    @inlineCallbacks
    def reset_list(self):
        yield self.write("SOURce1:LIST:RES")
    
    @inlineCallbacks
    def set_phase(self, phase):
        phase = round(phase, 1)
        if not -359.9<=phase<=359.9: raise Exception ("Phase out of range")
        yield self.write('SOURce:PHASe {}DEG'.format(phase))
        self.phase = phase
            
class RohdeSchwarzServer(GPIBManagedServer):
    """Provides basic CW control for Rohde&Schwarz SMB100A RF Generators"""
    name = 'RohdeSchwarz Server'
    deviceName = 'Rohde&Schwarz SMB100A'
    deviceWrapper = RSSMB100AWrapper

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
    
    @setting(13,'Activate List Mode', state = 'b', returns = '')
    def activate_list(self, c, state):
        """Activate the List Mode"""
        dev = self.selectedDevice(c)
        yield dev.activate_list_mode(state)
#        if bool(state):
#            #make sure the list goes to the first index after programming
#            print 'resetting'
#            yield dev.reset_list()
    
    @setting(14,"Reset List", returns = '')
    def reset_list(self, c):
        """Reset the List for List Mode"""
        dev = self.selectedDevice(c)
        yield dev.reset_list()
        
    @setting(15,"New List", inputs = '*(vv)', name = 's', returns = '')
    def make_new_list(self, c, inputs, name = 'unnamed'):
        """Make a new list, input is a list of tuples in the form (freq in Mhz, power in dBm)"""
        dev = self.selectedDevice(c)
        yield dev.make_new_list(inputs.astuple, name)
       
    
    @setting(16,"Set Phase", phase = 'v', returns = '')
    def set_phase(self, c, phase):
        """Sets the phase of the output, useful for phase locked applications"""
        dev = self.selectDevice(c)
        yield dev.set_phase(phase)

__server__ = RohdeSchwarzServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
