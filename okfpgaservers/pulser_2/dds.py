from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
import array
from labrad.units import WithUnit
from errors import dds_access_locked

class DDS(LabradServer):
    
    """Contains the DDS functionality for the pulser server"""
    
    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')
    
    @inlineCallbacks
    def initializeDDS(self):
        self.api.initializeDDS()
        yield self._set_all_dds()
    
    @inlineCallbacks
    def _set_all_dds(self):
        for channel in self.dds_channels.itervalues():
            freq,ampl,in_use = (channel.frequency, channel.amplitude, channel.inSequenceUse)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setParameters, channel, freq, ampl, in_use)
        
    
    @setting(41, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.dds_channels.keys()
    
    @setting(43, "Amplitude", name= 's', amplitude = 'v[dBm]', returns = 'v[dBm]')
    def amplitude(self, c, name = None, amplitude = None):
        """Get or set the amplitude of the named channel or the selected channel"""
        #get the hardware channel
        channel = self._getChannel(c, name)
        if channel.inSequenceUse:
            raise dds_access_locked()
        if amplitude is not None:
            #setting the ampplitude
            amplitude = amplitude['dBm']
            self._checkRange('amplitude', channel, amplitude)
            if channel.state:
                #only send to hardware if the channel is on
                yield self._setAmplitude(channel, amplitude)
            channel.amplitude = amplitude
            self.notifyOtherListeners(c, (name, 'amplitude', channel.amplitude), self.on_dds_param)
        amplitude = WithUnit(channel.amplitude, 'dBm')
        returnValue(amplitude)

    @setting(44, "Frequency", name = 's', frequency = ['v[MHz]'], returns = ['v[MHz]'])
    def frequency(self, c, name = None, frequency = None):
        """Get or set the frequency of the named channel or the selected channel"""
        #get the hardware channel
        channel = self._getChannel(c, name)
        if channel.inSequenceUse:
            raise dds_access_locked()
        if frequency is not None:
            #setting the frequency
            frequency = frequency['MHz']
            self._checkRange('frequency', channel, frequency)
            if channel.state:
                #only send to hardware if the channel is on
                yield self._setFrequency(channel, frequency)
            channel.frequency = frequency
            self.notifyOtherListeners(c, (name, 'frequency', channel.frequency), self.on_dds_param)
        frequency = WithUnit(channel.frequency, 'MHz')
        returnValue(frequency)
    
    @setting(45, 'Add DDS Pulses',  values = ['*(sv[s]v[s]v[MHz]v[dBm]v[deg])'])
    def addDDSPulses(self, c, values):
        '''
        input in the form of a list [(name, start, duration, frequency, amplitude, phase)]
        '''
        sequence = c.get('sequence')
        if not sequence: raise Exception ("Please create new sequence first")
        for value in values:
            try:
                name,start,dur,freq,ampl = value
                phase  = WithUnit(0, 'deg')
            except ValueError:
                name,start,dur,freq,ampl,phase = value
            try:
                channel = self.dds_channels[name]
            except KeyError:
                raise Exception("Unknown DDS channel {}".format(name))
            start = start['s']
            dur = dur['s']
            freq = freq['MHz']
            ampl = ampl['dBm']
            phase = phase['deg']
            if freq == 0 or ampl == 0:
                freq = channel.allowedfreqrange[0]
                ampl = channel.off_amplitude
            else:
                self._checkRange('frequency', channel, freq)
                self._checkRange('amplitude', channel, ampl)
            sequence.add_dds_pulse(name, start, start + dur, freq, ampl, phase)
        
    @setting(46, 'Get DDS Amplitude Range', name = 's', returns = '(vv)')
    def getDDSAmplRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedamplrange
        
    @setting(47, 'Get DDS Frequency Range', name = 's', returns = '(vv)')
    def getDDSFreqRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedfreqrange
    
    @setting(48, 'Output', name= 's', state = 'b', returns =' b')
    def output(self, c, name = None, state = None):
        """To turn off and on the dds. Turning off the DDS sets the frequency and amplitude 
        to the off_parameters provided in the configuration.
        """
        channel = self._getChannel(c, name)
        if channel.inSequenceUse:
            raise dds_access_locked()
        if state is not None:
            yield self._setOutput(channel, state)
            channel.state = state
            self.notifyOtherListeners(c, (name, 'state', channel.state), self.on_dds_param)
        returnValue(channel.state)

    def _checkRange(self, t, channel, val):
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0]<= val <= r[1]: raise Exception ("Value {} is outside allowed range".format(val))
    
    def _getChannel(self,c, name):
        try:
            channel = self.dds_channels[name]
        except KeyError:
            raise Exception("Channel {0} not found".format(name))
        return channel
    
    @inlineCallbacks
    def _setAmplitude(self, channel, ampl):
        freq = channel.frequency
        yield self.inCommunication.run(self._setParameters, channel, freq, ampl, in_use = False)
        
    @inlineCallbacks
    def _setFrequency(self, channel, freq):
        ampl = channel.amplitude
        yield self.inCommunication.run(self._setParameters, channel, freq, ampl, in_use = False)
    
    @inlineCallbacks
    def _setOutput(self, channel, state):
        if state and not channel.state: #if turning on, and is currently off
            yield self.inCommunication.run(self._setParameters, channel, channel.frequency, channel.amplitude, in_use = False)
        elif (channel.state and not state): #if turning off and is currenly on
            freq,ampl = channel.off_parameters
            yield self.inCommunication.run(self._setParameters, channel, freq, ampl, in_use = False)
    
    @inlineCallbacks
    def _programDDSSequence(self, dds):
        '''takes the parsed dds sequence and programs the board with it'''
        for name,channel in self.dds_channels.iteritems():
            if name in dds:
                yield self.program_dds_chanel(channel, dds[name])
                channel.in_use = True
    
    @inlineCallbacks
    def _setParameters(self, channel, freq, ampl, in_use):
        buf = self.settings_to_buf(channel, freq, ampl, in_use)
        yield self.program_dds_chanel(channel, buf)
    
    def settings_to_buf(self, channel, freq, ampl, in_use):
        num = self.settings_to_num(channel, freq, ampl, in_use)
        buf = self._intToBuf_coherent(num)
        buf = buf + '\x00\x00' #adding termination
        return buf
    
    def settings_to_num(self, channel, freq, ampl, in_use, phase = 0.0):
        num = self._valToInt_coherent(channel, in_use, freq, ampl, phase)
        return num
    
    @inlineCallbacks
    def program_dds_chanel(self, channel, buf):
        addr = channel.channelnumber
        if not channel.remote:
            yield deferToThread(self._setDDSLocal, addr, buf)
        else:
            yield self._setDDSRemote(channel, addr, buf)
    
    def _setDDSLocal(self, addr, buf):
        self.api.resetAllDDS()
        self.api.setDDSchannel(addr)  
        self.api.programDDS(buf)
    
    @inlineCallbacks
    def _setDDSRemote(self, channel, addr, buf):
        cxn = self.remoteConnections[channel.remote]
        remote_info = self.remote_dds_channels[channel.remote]
        server, reset, program = remote_info.server, remote_info.reset, remote_info.program
        try:
            yield cxn.servers[server][reset]()
            yield cxn.servers[server][program]([(channel.channelnumber, buf)])
        except (KeyError,AttributeError):
            print 'Not programing remote channel {}'.format(channel.remote)
    
    @inlineCallbacks
    def unlock_dds_channels(self):
        for channel in self.dds_channels.itervalues():
            channel.in_use = False
        yield self._set_all_dds()
    
    def _getCurrentDDS(self, channels):
        '''
        Returns a dictionary {name:num} with the reprsentation of the current dds state
        '''
        current = [(name, self._channel_to_num(channel, in_use = True)) for (name,channel) in self.dds_channels.iteritems() if name in channels]
        return dict(current)
    
    def _channel_to_num(self, channel, in_use):
        '''returns the current state of the channel in the num represenation. Ignore the in-use bit'''
        if channel.state:
            #if on, use current values. else, use off values
            freq,ampl = (channel.frequency, channel.amplitude)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
        else:
            freq,ampl = channel.off_parameters
        num = self.settings_to_num(channel, freq, ampl, in_use)
        return num
 
    def _valToInt_coherent(self, channel, in_use, freq, ampl, phase):
        '''
        takes the frequency and amplitude values for the specific channel and returns integer representation of the dds setting
        freq is in MHz
        power is in dbm
        '''
        ans = 0
        for val,r,m, precision in [(freq,channel.boardfreqrange, 1, 32), (ampl,channel.boardamplrange, 2 ** 32,  16), (phase,channel.boardphaserange, 2 ** 48,  16)]:
            minim, maxim = r
            resolution = (maxim - minim) / float(2**precision - 1)
            seq = int((val - minim)/resolution) #sequential representation
            ans += m*seq
        if not in_use: ans+=2**31 #set the most significant bit to 1 
        return ans
    
    def _intToBuf_coherent(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''
        freq_num = num % 2**32
        a, b = freq_num // 2**16, freq_num % 2**16
        freq_arr = array.array('B', [b % 256 ,b // 256, a % 256, a // 256])
        
        phase_ampl_num = num // 2**32
        a, b = phase_ampl_num // 256**2, phase_ampl_num % 256**2
        phase_ampl_arr = array.array('B', [a % 256 ,a // 256, b % 256, b // 256])
        
        ans = phase_ampl_arr.tostring() + freq_arr.tostring()
        return ans