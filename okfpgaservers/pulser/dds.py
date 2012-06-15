from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
import array

class DDS(LabradServer):
    """Contains the DDS functionality for the pulser server"""
    
    def initializeDDS(self):
        self._initializeDDS()
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
        print 'programming dds now'
        for config in self.ddsDict.itervalues():
            chan = config.channelnumber
            buf = dds[chan]
            print chan,[buf]
            self._resetAllDDS()
            self._setDDSchannel(chan)
            self._programDDS(buf)
            
    def _setParameters(self, chan, freq, ampl):
        import time
        #####
        self._resetAllDDS()
        addr = self.ddsDict[chan].channelnumber
        print 'setting chan', addr
        self._setDDSchannel(addr)  
        num = self._valToInt(chan, freq, ampl)
        print num
        buf = self._intToBuf(num)
        buf = buf + '\x00\x00' #adding termination
        print [buf]
        self._programDDS(buf)
    
    def _addDDSInitial(self, seq):
        for chan in self.ddsDict.iterkeys():
            freq,ampl = (self.ddsDict[chan].frequency, self.ddsDict[chan].amplitude)
            self._checkRange('amplitude', chan, ampl)
            self._checkRange('frequency', chan, freq)
            addr = self.ddsDict[chan].channelnumber
            num = self._valToInt(chan, freq, ampl)
            seq.addDDS(addr, 0, num)
        
    def _valToInt(self, chan, freq, ampl):
        '''
        takes the frequency and amplitude values for the specific channel and returns integer representation of the dds setting
        freq is in MHz
        power is in dbm
        '''
        config = self.ddsDict[chan]
        ans = 0
        for val,r,m in [(freq,config.boardfreqrange, 256**2), (ampl,config.boardamplrange, 1)]:
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
        #print arr
        ans = arr.tostring()
        return ans
    
    def _resetAllDDS(self):
        '''Reset the ram position of all dds chips to 0'''
        self.xem.ActivateTriggerIn(0x40,4)
    
    def _advanceAllDDS(self):
        '''Advance the ram position of all dds chips'''
        self.xem.ActivateTriggerIn(0x40,5)
    
    def _setDDSchannel(self, chan):
        '''select the dds chip for communication'''
        self.xem.SetWireInValue(0x04,chan)
        self.xem.UpdateWireIns()
    
    def _programDDS(self, prog):
        '''program the dds channel with a list of frequencies and amplitudes. The channel of the particular channel must be selected first'''
        self.xem.WriteToBlockPipeIn(0x81, 2, prog)
    
    def _initializeDDS(self):
        '''force reprogram of all dds chips during initialization'''
        self.xem.ActivateTriggerIn(0x40,6)