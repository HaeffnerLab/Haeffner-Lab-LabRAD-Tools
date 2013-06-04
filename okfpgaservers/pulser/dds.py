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
        self.ddsLock = False
        self.api.initializeDDS()
        for name,channel in self.ddsDict.iteritems():
            channel.name = name
            freq,ampl = (channel.frequency, channel.amplitude)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setParameters, channel, freq, ampl)
    
    @setting(41, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()
    
    @setting(43, "Amplitude", name= 's', amplitude = 'v[dBm]', returns = 'v[dBm]')
    def amplitude(self, c, name = None, amplitude = None):
        """Get or set the amplitude of the named channel or the selected channel"""
        #get the hardware channel
        if self.ddsLock and amplitude is not None: 
            raise dds_access_locked()
        channel = self._getChannel(c, name)
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
        if self.ddsLock and frequency is not None: 
            raise dds_access_locked()
        channel = self._getChannel(c, name)
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
                phase  = 0.0
            except ValueError:
                name,start,dur,freq,ampl,phase = value
            try:
                channel = self.ddsDict[name]
            except KeyError:
                raise Exception("Unknown DDS channel {}".format(name))
            start = start['s']
            dur = dur['s']
            freq = freq['MHz']
            ampl = ampl['dBm']
            phase = phase['deg']
            freq_off, ampl_off = channel.off_parameters
            if freq == 0 or ampl == 0: #off state
                freq, ampl = freq_off,ampl_off
            else:
                self._checkRange('frequency', channel, freq)
                self._checkRange('amplitude', channel, ampl)
            num = self.settings_to_num(channel, freq, ampl, phase)
            if not channel.phase_coherent_model:
                num_off = self.settings_to_num(channel, freq_off, ampl_off)
            else:
                #note that keeping the frequency the same when switching off to preserve phase coherence
                num_off = self.settings_to_num(channel, freq, ampl_off, phase) 
            #note < sign, because start can not be 0. 
            #this would overwrite the 0 position of the ram, and cause the dds to change before pulse sequence is launched
            if not self.sequenceTimeRange[0] < start <= self.sequenceTimeRange[1]: 
                raise Exception ("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start))
            if not self.sequenceTimeRange[0] < start + dur <= self.sequenceTimeRange[1]: 
                raise Exception ("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start + dur))
            if not dur == 0:#0 length pulses are ignored
                sequence.addDDS(name, start, num, 'start')
                sequence.addDDS(name, start + dur, num_off, 'stop')
        
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
        if self.ddsLock and state is not None: 
            raise dds_access_locked()
        channel = self._getChannel(c, name)
        if state is not None:
            yield self._setOutput(channel, state)
            channel.state = state
            self.notifyOtherListeners(c, (name, 'state', channel.state), self.on_dds_param)
        returnValue(channel.state)
    
    @setting(49, 'Clear DDS Lock')
    def clear_dds_lock(self, c):
        self.ddsLock = False
    
    def _checkRange(self, t, channel, val):
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0]<= val <= r[1]: raise Exception ("channel {0} : {1} of {2} is outside the allowed range".format(channel.name, t, val))
    
    def _getChannel(self,c, name):
        try:
            channel = self.ddsDict[name]
        except KeyError:
            raise Exception("Channel {0} not found".format(name))
        return channel
    
    @inlineCallbacks
    def _setAmplitude(self, channel, ampl):
        freq = channel.frequency
        yield self.inCommunication.run(self._setParameters, channel, freq, ampl)
        
    @inlineCallbacks
    def _setFrequency(self, channel, freq):
        ampl = channel.amplitude
        yield self.inCommunication.run(self._setParameters, channel, freq, ampl)
    
    @inlineCallbacks
    def _setOutput(self, channel, state):
        if state and not channel.state: #if turning on, and is currently off
            yield self.inCommunication.run(self._setParameters, channel, channel.frequency, channel.amplitude)
        elif (channel.state and not state): #if turning off and is currenly on
            freq,ampl = channel.off_parameters
            yield self.inCommunication.run(self._setParameters, channel, freq, ampl)
    
    @inlineCallbacks
    def _programDDSSequence(self, dds):
        '''takes the parsed dds sequence and programs the board with it'''
        self.ddsLock = True
        for name,channel in self.ddsDict.iteritems():
            buf = dds[name]
            yield self.program_dds_chanel(channel, buf)
    
    @inlineCallbacks
    def _setParameters(self, channel, freq, ampl):
        buf = self.settings_to_buf(channel, freq, ampl)
        yield self.program_dds_chanel(channel, buf)
    
    def settings_to_buf(self, channel, freq, ampl):
        num = self.settings_to_num(channel, freq, ampl)
        if not channel.phase_coherent_model:
            buf = self._intToBuf(num)
        else:
            buf = self._intToBuf_coherent(num)
        buf = buf + '\x00\x00' #adding termination
        return buf
    
    def settings_to_num(self, channel, freq, ampl, phase = 0.0):
        if not channel.phase_coherent_model:
            num = self._valToInt(channel, freq, ampl)
        else:
            num = self._valToInt_coherent(channel, freq, ampl, phase)
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
        remote_info = self.remoteChannels[channel.remote]
        server, reset, program = remote_info.server, remote_info.reset, remote_info.program
        try:
            yield cxn.servers[server][reset]()
            yield cxn.servers[server][program]([(channel.channelnumber, buf)])
        except (KeyError,AttributeError):
            print 'Not programing remote channel {}'.format(channel.remote)
    
    def _getCurrentDDS(self):
        '''
        Returns a dictionary {name:num} with the reprsentation of the current dds state
        '''
        d = dict([(name,self._channel_to_num(channel)) for (name,channel) in self.ddsDict.iteritems()])
        return d
    
    def _channel_to_num(self, channel):
        '''returns the current state of the channel in the num represenation'''
        if channel.state:
            #if on, use current values. else, use off values
            freq,ampl = (channel.frequency, channel.amplitude)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
        else:
            freq,ampl = channel.off_parameters
        num = self.settings_to_num(channel, freq, ampl)
        return num
        
    def _valToInt(self, channel, freq, ampl):
        '''
        takes the frequency and amplitude values for the specific channel and returns integer representation of the dds setting
        freq is in MHz
        power is in dbm
        '''
        ans = 0
        for val,r,m in [(freq,channel.boardfreqrange, 256**2), (ampl,channel.boardamplrange, 1)]:
            minim, maxim = r
            resolution = (maxim - minim) / float(16**4 - 1)
            seq = int((val - minim)/resolution) #sequential representation
            ans += m*seq
        return ans
    
    def _intToBuf(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''
        #converts value to buffer string, i.e 128 -> \x00\x00\x00\x80
        a, b = num // 256**2, num % 256**2
        arr = array.array('B', [a % 256 ,a // 256, b % 256, b // 256])
        ans = arr.tostring()
        return ans
    
    def _valToInt_coherent(self, channel, freq, ampl, phase = 0):
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
        return ans
    
    def _intToBuf_coherent(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''
        freq_num = num % 2**32
        a, b = freq_num // 256**2, freq_num % 256**2
        freq_arr = array.array('B', [b % 256 ,b // 256, a % 256, a // 256])
        
        phase_ampl_num = num // 2**32
        a, b = phase_ampl_num // 256**2, phase_ampl_num % 256**2
        phase_ampl_arr = array.array('B', [a % 256 ,a // 256, b % 256, b // 256])
        
        ans = phase_ampl_arr.tostring() + freq_arr.tostring()
        return ans