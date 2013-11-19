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
version = 1.15
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
        self.modulation_state = yield self.getModulationState()
        self.modulation_type = yield self.getModulationType()
        self.psk_modulation_source = yield self.getPSKModSource()
        self.phase = yield self.getPhase()
        self.psk_phase = yield self.getPSKPhase()
        self.state = yield self.getState()
    
    @inlineCallbacks
    def getState(self):
        state_string = yield self.query('OUTPut1:STATe?\n')
        if state_string == 'OFF':
            state = False
        elif state_string == 'ON':
            state = True
        else:
            raise Exception("Incorrect State")
        returnValue(state)
    
    @inlineCallbacks
    def setState(self, state):
        print 'setting state to', state
        if state:
            yield self.write('OUTPut1:STATe ON\n')
        else:
            yield self.write('OUTPut1:STATe OFF\n')
        self.state = state
    
    @inlineCallbacks
    def getPSKPhase(self):
        psk_phase = yield self.query('SOURce1:MOD:PSKey:PHASe?\n').addCallback(float)
        psk_phase = WithUnit(psk_phase, 'deg')
        returnValue(psk_phase)
    
    @inlineCallbacks
    def setPSKPhase(self, psk_phase):
        if not 0<=psk_phase['deg']<=360:
            raise Exception("Incorrect PSK Phase")
        yield self.write('SOURce1:MOD:PSKey:PHASe {0:.1f}\n'.format(psk_phase['deg']))
        self.psk_phase = psk_phase
        
    
    @inlineCallbacks
    def getPhase(self):
        phase = yield self.query('SOURce1:PHASe?\n').addCallback(float)
        phase = WithUnit(phase, 'deg') 
        returnValue(phase)
    
    @inlineCallbacks
    def setPhase(self, phase):
        if not 0<=phase['deg']<=360:
            raise Exception("Incorrect Phase")
        yield self.write('SOURce1:PHASe {0:.1f}\n'.format(phase['deg']))
        self.phase = phase
        
    @inlineCallbacks
    def getModulationState(self):
        state_string = yield self.query('SOURce1:MOD:STATe?\n')
        if state_string == 'OFF':
            state = False
        elif state_string == 'ON':
            state = True
        else:
            raise Exception("Incorrect State")
        returnValue(state)
    
    @inlineCallbacks
    def setModulationState(self, state):
        if state:
            yield self.write('SOURce1:MOD:STATe ON\n')
        else:
            yield self.write('SOURce1:MOD:STATe OFF\n')
        self.modulation_state = state
    
    @inlineCallbacks
    def getModulationType(self):
        mod_type = yield self.query('SOURce1:MOD:TYPe?\n')
        returnValue(mod_type)
    
    @inlineCallbacks
    def setModulationType(self, mod_type):
        if mod_type not in ['AM','FM','PM','ASK','FSK','PSK','PWM','BPSK','QPSK','3FSK','4FSK','OSK']:
            raise Exception("Incorrect modulation type")
        yield self.write('SOURce1:MOD:TYPe {}\n'.format(mod_type))
        self.modulation_type = mod_type
    
    @inlineCallbacks
    def setPSKModSource(self, source):
        if source not in ['internal', 'external']:
            raise Exception("Incorrect source")
        yield self.write('SOURce1:MOD:PSKey:SOURce {}\n'.format(source[:3].upper()))
        self.psk_modulation_source = source 
    
    @inlineCallbacks
    def getPSKModSource(self):
        source = yield self.query('SOURce1:MOD:PSKey:SOURce?\n')
        source = '{}ernal'.format(source.lower())
        returnValue(source)
    
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
    
    @setting(11, 'Output', state = 'b', returns='b')
    def output(self, c, state=None):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if state is not None:
            yield dev.setState(state)
        returnValue(dev.state)
    
    @setting(21, 'Modulation State', state = 'b', returns = 'b')
    def modulation_state(self, c, state = None):
        '''Get or set the state of the modulation'''
        dev = self.selectedDevice(c)
        if state is not None:
            yield dev.setModulationState(state)
        returnValue(dev.modulation_state)
    
    @setting(22, "Modulation Type", mod_type = 's', returns = 's')
    def modulation_type(self, c, mod_type = None):
        '''Get or set the modulation type'''
        dev = self.selectedDevice(c)
        if mod_type is not None:
            yield dev.setModulationType(mod_type)
        returnValue(dev.modulation_type)
    
    @setting(23, "PSK Modulation Source", psk_mod_source = 's', returns = 's')
    def modulation_psk_source(self, c, psk_mod_source = None):
        dev = self.selectedDevice(c)
        if psk_mod_source is not None:
            yield dev.setPSKModSource(psk_mod_source)
        returnValue(dev.psk_modulation_source)
    
    @setting(24, "Phase", phase = 'v[deg]', returns = 'v[deg]')
    def phase(self, c, phase = None):
        dev = self.selectedDevice(c)
        if phase is not None:
            yield dev.setPhase(phase)
        returnValue(dev.phase)
    
    @setting(25, 'PSK Phase', psk_phase = 'v[deg]', returns = 'v[deg]')
    def psk_phase(self, c, psk_phase = None):
        dev = self.selectedDevice(c)
        if psk_phase is not None:
            yield dev.setPSKPhase(psk_phase)
        returnValue(dev.psk_phase)

__server__ = RigolDG4062Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
