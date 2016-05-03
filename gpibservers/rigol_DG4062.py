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
version = 1.20
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
        self.burst_state = yield self.getBurstState()
        self.burst_gate_polarity = yield self.getBurstGatePolarity()
        self.burst_phase = yield self.getBurstPhase()
        self.burst_mode = yield self.getBurstMode()
        
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
    def setFrequency(self, f,source):
        if self.frequency != f:
            yield self.write('SOURce'+str(source)+':FREQuency:FIXed {0}\n'.format(f['Hz']))
            self.frequency = f
    
    @inlineCallbacks
    def getBurstState(self):
        state_string = yield self.query('SOURce1:BURSt:STATe?\n')
        if state_string == 'OFF':
            state = False
        elif state_string == 'ON':
            state = True
        else:
            raise Exception("Incorrect State")
        returnValue(state)
    
    @inlineCallbacks
    def setBurstState(self, burst_state, source):
        if burst_state:
            yield self.write('SOURce'+str(source)+':BURSt:STATe ON\n')
        else:
            yield self.write('SOURce'+str(source)+':BURSt:STATe OFF\n')
        self.burst_state = burst_state
    
    @inlineCallbacks
    def getBurstGatePolarity(self):
        polarity_string = yield self.query('SOURce1:BURST:GATE:POLarity?\n')
        if polarity_string == 'NORM':
            polarity = 'normal'
        elif polarity_string == 'INV':
            polarity = 'inverted'
        else:
            raise Exception("Incorrect poalrity {}".format(polarity_string))
        returnValue(polarity)
    
    @inlineCallbacks
    def setBurstGatePolarity(self, burst_gate_polarity):
        if burst_gate_polarity == 'normal':
            polarity_string = 'NORM'
        elif burst_gate_polarity == 'inverted':
            polarity_string = 'INV'
        else:
            raise Exception("Wrong Gated Polarity {}".format(burst_gate_polarity))
        yield self.write('SOURce1:BURST:GATE:POLarity {}\n'.format(polarity_string)) 
        self.burst_gate_polarity = burst_gate_polarity
    
    @inlineCallbacks
    def getBurstPhase(self):
        phase = yield self.query('SOURce1:BURSt:PhASe?\n').addCallback(float)
        phase = WithUnit(phase, 'deg') 
        returnValue(phase)
    
    @inlineCallbacks
    def setBurstPhase(self, phase):
        if not 0<=phase['deg']<=360:
            raise Exception("Incorrect Phase")
        yield self.write('SOURce1:BURSt:PHASe {0:.1f}\n'.format(phase['deg']))
        self.burst_phase = phase
    
    @inlineCallbacks
    def getBurstMode(self):
        mode_str = yield self.query('SOURCe1:BURSt:MODE?\n')
        if mode_str == 'GAT':
            burst_mode = 'gated'
        elif mode_str == 'TRIG':
            burst_mode = 'triggered'
        elif mode_str == 'INF':
            burst_mode = 'infinity'
        else:
            raise Exception("Incorrect mode")
        returnValue(burst_mode)

    @inlineCallbacks
    def setBurstCycles(self, cycles):
        yield self.write('BURST:NCYCles {}'.format(int(cycles)))

    @inlineCallbacks
    def trigger(self):
        yield self.write('*TRG')

    @inlineCallbacks
    def setBurstMode(self, burst_mode, source):
        if burst_mode == 'gated':
            burst_str = 'GAT'
        elif burst_mode == 'triggered':
            burst_str = 'TRIG'
        elif burst_mode == 'infinity':
            burst_str = 'INF'
        yield self.write('SOURc'+str(source)+':BURSt:MODE {}'.format(burst_str))
        self.burst_mode = burst_mode

    @inlineCallbacks
    def setArbitraryWaveform(self, s, source):
        comstr = 'DATA VOLATILE, '
        yield self.write(comstr + s)
        # now select the waveform in volatile memory
        yield self.write('SOURce'+str(source)+':FUNction USER')

    @inlineCallbacks
    def setVoltage(self, voltage, source):
        """Writes out the voltage in Vpp"""
        yield self.write('SOURce'+str(source)+'VOLTage')
 
class RigolDG4062Server(GPIBManagedServer):
    """Provides basic CW control for Rigol Signal Generators"""
    name = 'Rigol DG4062 Server'
    deviceName = 'Rigol Technologies DG4062'
    deviceWrapper = RigolDG4062Wrapper

    @setting(10, 'Frequency', f=['v[MHz]'], source='i', returns=['v[MHz]'])
    def frequency(self, c, f=None, source=1):
        """Get or set the CW frequency."""
        dev = self.selectedDevice(c)
        if f is not None:
            yield dev.setFrequency(f,source)
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
        
    '''
    Settings 30 to 40 are related to the BURST mode
    '''
    @setting(30, 'Burst State', burst_state ='b', source='i', returns = 'b')
    def burst_state(self, c, burst_state = None, source=1):
        '''Set of get the state of the burst mode'''
        dev = self.selectedDevice(c)
        if burst_state is not None:
            yield dev.setBurstState(burst_state, source)
        returnValue(dev.burst_state)
    
    @setting(31, 'Burst Gate Polarity', burst_gate_polarity ='s', returns = 's')
    def burst_gate_polarity(self, c, burst_gate_polarity = None):
        '''Set of get the state of the burst mode. Can be 'normal' or 'inverted' '''
        dev = self.selectedDevice(c)
        if burst_gate_polarity is not None:
            yield dev.setBurstGatePolarity(burst_gate_polarity)
        returnValue(dev.burst_gate_polarity)
    
    @setting(32, 'Burst Phase', burst_phase = 'v[deg]', returns = 'v[deg]')
    def burst_phase(self, c, burst_phase = None):
        '''Set or get the phase of the burst'''
        dev = self.selectedDevice(c)
        if burst_phase is not None:
            yield dev.setBurstPhase(burst_phase)
        returnValue(dev.burst_phase)
    
    @setting(33, 'Burst Mode', burst_mode = 's', source='i', returns = 's')
    def burst_mode(self, c, burst_mode = None, source='i'):
        '''Set or get the burst mode of the device. Can be 'triggered', 'gated' or 'infinity' '''
        dev = self.selectedDevice(c)
        if burst_mode is not None:
            yield dev.setBurstMode(burst_mode, source)
        returnValue(dev.burst_mode)

    @setting(34, 'Burst Cycles', cycles='i', returns = '')
    def burst_mode(self, c, cycles):
        '''Set or get the burst mode of the device. Can be 'triggered', 'gated' or 'infinity' '''
        dev = self.selectedDevice(c)
        yield dev.setBurstCycles(cycles)

    @setting(35, 'Trigger', returns = '')
    def trigger(self, c):
        '''Set or get the burst mode of the device. Can be 'triggered', 'gated' or 'infinity' '''
        dev = self.selectedDevice(c)
        yield dev.trigger()



    '''
    Settings 40 to 50 are related to ARB mode
    '''

    @setting(40, 'Arbitrary waveform', s = 's', source='i', returns = '')
    def arbitrary_waveform(self, c, s, source=1):
        """
        Pass a string of amplitudes. Load waveform into volatile memory
        and select the waveform in volatile memory.
        """
        dev = self.selectedDevice(c)
        yield dev.setArbitraryWaveform(s,source)

    @setting(41, 'Voltage', voltage = 'v[V]', source='i', returns = '')
    def arbitrary_waveform(self, c, voltage, source=1):
        """
        Pass a string of amplitudes. Load waveform into volatile memory
        and select the waveform in volatile memory.
        """
        dev = self.selectedDevice(c)
        yield dev.setVoltage(voltage,source)
    

__server__ = RigolDG4062Server()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
