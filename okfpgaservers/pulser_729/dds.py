from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
import array

class DDS(LabradServer):
    """Contains the DDS functionality for the pulser server"""
    
    def initializeDDS(self):
        self.ddsLock = False #boolean whether or not dds can be changed. will be used to block access while pulse sequence is programmed or running.
        self.api.initializeDDS()
        for chan in self.ddsDict.iterkeys():
            freq,ampl = (self.ddsDict[chan].frequency, self.ddsDict[chan].amplitude)
            self._checkRange('amplitude', chan, ampl)
            self._checkRange('frequency', chan, freq)
            self._setParameters(chan, freq, ampl)
    
    @setting(41, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()
    
    @setting(42, "Select DDS Channel", name = 's')
    def selectChannel(self, c, name):
        if name not in self.ddsDict.keys(): raise Exception("Incorrect DDS Channel {}".format(name))
        c['ddschan'] = name
    
    @setting(43, "Amplitude", amplitude = 'v[dBm]', returns = 'v[dBm]')
    def amplitude(self, c, amplitude = None):
        """Get or Set the amplitude of the named channel, or of the channel selected in the current context"""
        #get the hardware channel
        if self.ddsLock: 
            self.ddsLock = False
            raise Exception("DDS access is locked. Running pulse sequence.")
        name = c.get('ddschan')
        if name is None: raise Exception ("Channel not provided and not selected")
        if amplitude is not None:
            #set the amplitude
            amplitude = amplitude.inUnitsOf('dBm')
            amplitude = float( amplitude )
            self._checkRange('amplitude', name, amplitude)
            yield self._setAmplitude(name, amplitude)
            self.ddsDict[name].amplitude = amplitude
        #return the current amplitude
        amplitude = self.ddsDict[name].amplitude
        returnValue(amplitude)

    @setting(44, "Frequency", frequency = ['v[MHz]'], returns = ['v[MHz]'])
    def frequency(self, c, frequency = None):
        """Get or Set the frequency of the named channel, or of the channel selected in the current context"""
        #get the hardware channel
        if self.ddsLock: 
            self.ddsLock = False
            raise Exception("DDS access is locked. Running pulse sequence.")
        name = c.get('ddschan')
        if name is None: raise Exception ("Channel not provided and not selected")
        if frequency is not None:
            #set the amplitude
            frequency = frequency.inUnitsOf('MHz')
            frequency = float( frequency )
            self._checkRange('frequency', name, frequency)
            yield self._setFrequency(name, frequency)
            self.ddsDict[name].frequency = float(frequency)
        #return the current amplitude
        frequency = self.ddsDict[name].frequency
        returnValue(frequency)
    
    @setting(45, 'Add DDS Pulses', channel = 's', values = '*(vvv)')
    def addDDSPulse(self, c, channel, values):
        """Takes the name of the DDS channel, and the list of values in the form [(start, frequency, amplitude)]
        where frequency is in MHz, and amplitude is in dBm
        """
        if channel not in self.ddsDict.keys(): raise Exception("Unknown DDS channel {}".format(channel))
        hardwareAddr = self.ddsDict.get(channel).channelnumber
        sequence = c.get('sequence')
        #simple error checking
        if not sequence: raise Exception ("Please create new sequence first")
        for start,freq,ampl in values:
            sett = self._valToInt(channel, freq, ampl)
            sequence.addDDS(hardwareAddr, start, sett)
    
    @setting(46, 'Get DDS Amplitude Range', returns = '(vv)')
    def getDDSAmplRange(self, c):
        name = c.get('ddschan')
        if name is None: raise Exception ("Channel not provided and not selected")
        return self.ddsDict[name].allowedamplrange
        
    @setting(47, 'Get DDS Frequency Range', returns = '(vv)')
    def getDDSFreqRange(self, c):
        name = c.get('ddschan')
        if name is None: raise Exception ("Channel not provided and not selected")
        return self.ddsDict[name].allowedfreqrange
    
    def _checkRange(self, t, name, val):
        if t == 'amplitude':
            r = self.ddsDict[name].allowedamplrange
        elif t == 'frequency':
            r = self.ddsDict[name].allowedfreqrange
        if not r[0]<= val <= r[1]: raise Exception ("Value {} is outside allowed range".format(val))
    
    @inlineCallbacks
    def _setAmplitude(self, chan, ampl):
        freq = self.ddsDict[chan].frequency
        yield self.inCommunication.acquire()
        yield deferToThread(self._setParameters, chan, freq, ampl)
        self.inCommunication.release()
        
    @inlineCallbacks
    def _setFrequency(self, chan, freq):
        ampl = self.ddsDict[chan].amplitude
        yield self.inCommunication.acquire()
        yield deferToThread(self._setParameters, chan, freq, ampl)
        self.inCommunication.release()
    
    def _programDDSSequence(self, dds):
        '''takes the parsed dds sequence and programs the board with it'''
        self.ddsLock = True
        for config in self.ddsDict.itervalues():
            chan = config.channelnumber
            buf = dds[chan]
            self.api.resetAllDDS()
            self.api.setDDSchannel(chan)
            self.api.programDDS(buf)
            
    def _setParameters(self, chan, freq, ampl):
        self.api.resetAllDDS()
        addr = self.ddsDict[chan].channelnumber
        self.api.setDDSchannel(addr)  
        num = self._valToInt(chan, freq, ampl)
        buf = self._intToBuf(num)
        buf = buf + '\x00\x00' #adding termination
        self.api.programDDS(buf)
    
    def _addDDSInitial(self, seq):
        for chan in self.ddsDict.iterkeys():
            freq,ampl = (self.ddsDict[chan].frequency, self.ddsDict[chan].amplitude)
            self._checkRange('amplitude', chan, ampl)
            self._checkRange('frequency', chan, freq)
            addr = self.ddsDict[chan].channelnumber
            num = self._valToInt(chan, freq, ampl)
            seq.addDDS(addr, 0, num)
        
    def _valToInt(self, chan, freq, ampl, phase = 0):
        '''
        takes the frequency and amplitude values for the specific channel and returns integer representation of the dds setting
        freq is in MHz
        power is in dbm
        '''
        config = self.ddsDict[chan]
        ans = 0
        for val,r,m, precision in [(freq,config.boardfreqrange, 1, 32), (ampl,config.boardamplrange, 2 ** 32,  16), (phase,config.boardphaserangge, 2 ** 48,  16)]:
            minim, maxim = r
            resolution = (maxim - minim) / float(2**precision - 1)
            seq = int((val - minim)/resolution) #sequential representation
            ans += m*seq
        return ans
    
    def _intToBuf(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''
        freq_num = num // 2**32
        a, b = freq_num // 256**2, freq_num % 256**2
        freq_arr = array.array('B', [b % 256 ,b // 256, a % 256, a // 256])
        
        phase_ampl_num = num // 2**32
        a, b = phase_ampl_num // 256**2, phase_ampl_num % 256**2
        phase_ampl_arr = array.array('B', [a % 256 ,a // 256, b % 256, b // 256])
        
        ans = phase_ampl_arr.tostring() + freq_arr.to_string()
        return ans
    
#xem.ActivateTriggerIn(0x40,6) #reprogram DDS, implement separately
#xem.ActivateTriggerIn(0x40,4) #reset RAM to position 0 
#xem.SetWireInValue(0x04,0x00) #set channel
#xem.UpdateWireIns()
#
#data1 = "\x00\x00\xff\xff"
#freq = 220.0  ### in MHz
#
##absolute #0 < freq < 400
##190 < freq < 250
##switching - both
#
##ampl: -63 < x < -3
#
##phase: 16 bit repr of 0-360
#
#
#a, b = freq_round // 256**2, freq_round % 256**2
#arr = array.array('B', [b % 256 ,b // 256, a % 256, a // 256])
#data2 = arr.tostring()
#data = data1 + data2

####phase: \xLSB\xMSB amplitude: \xLSB\xMSB freq: \xLSB\xlSB\xmSB\xMSB

### data = "\x00\x00\x00\x80\x00\x00x\00x\80"



#xem.WriteToBlockPipeIn(0x81, 2, data)
#
#xem.WriteToBlockPipeIn(0x81, 2, "\x00\x00") #terminate