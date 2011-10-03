"""
### BEGIN NODE INFO
[info]
name = Double Pass
version = 1.0
description = 
instancename = Double Pass

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

SIGNALID = 19811

class doublePass(object):
    """when subclassing need to implement:
        self.freqFunc #function for setting the frequency in MHZ
        self.amplFunc #function for setting the amplitude in DM
        self.outputFunc #function for setting the output using True/False
    """
    def __init__(self, name):
        self.name = name
        self.freq = None
        self.ampl = None
        self.outp = None
        self.amplOffset = 0
        self.freqToCalibAmpl = None #function to get calibrated amplitude for the given frequency
        self.freqRange = None
        self.amplRange = None
         
    @inlineCallbacks
    def populateInfo(self):
        self.freq = yield self.freqFunc()
        self.ampl = yield self.amplFunc()
        self.outp = yield self.outputFunc()
    
    @inlineCallbacks
    def frequency(self, freq):
        if freq is not None:
            if not self.freqRange[0] <= freq <= self.freqRange[1]: raise Exception ("Frequency out of range")
            yield self.freqFunc(freq)
            self.freq = freq
        returnValue( self.freq)
    
    @inlineCallbacks
    def amplitude(self, ampl):
        if ampl is not None:
            if not self.amplRange[0] <= ampl <= self.amplRange[1]: raise Exception ("Amplitude out of range")
            yield self.amplFunc(ampl)
            self.ampl = ampl
        returnValue( self.ampl)
    
    @inlineCallbacks
    def output(self, output):
        if output is not None:
            yield self.outputFunc(output)
            self.outp = output
        returnValue( self.outp)

    @inlineCallbacks
    def frequencyCalibPower(self, freq):
        yield self.frequency(freq)
        calibAmpl = self.freqToCalibAmpl(freq) + self.amplOffset
        yield self.amplitude(calibAmpl) 
        returnValue ((self.freq, self.ampl))
    
    @inlineCallbacks
    def amplitudeOffset(self, offset):
        self.amplOffset = offset
        yield self.frequencyCalibPower(self.freq)
        returnValue ((self.freq, self.ampl))
        
class global397(doublePass):
    def __init__(self, name, cxn, context):
        super(global397,self).__init__(name)
        self.selectFuncs(cxn, context)
    
    @inlineCallbacks
    def selectFuncs(self, cxn, context):
        self.server = cxn.rohdeschwarz_server
        self.context = context
        yield self.server.select_device('lattice-pc GPIB Bus - USB0::0x0AAD::0x0054::104542', context = self.context)
        self.freqRange = (95,125) #MHZ
        self.amplRange = (-145,24) #dBM
        yield self.populateInfo()
        
    @inlineCallbacks
    def freqFunc(self, freq = None):
        freq = yield self.server.frequency(freq, context = self.context)
        returnValue(freq) 
    
    @inlineCallbacks
    def amplFunc(self, ampl = None):
        ampl = yield self.server.amplitude(ampl, context = self.context)
        returnValue(ampl)
    
    @inlineCallbacks
    def outputFunc(self, outp= None):
        outp = yield self.server.output(outp, context = self.context)
        returnValue(outp)    
    
    #no calibration, that is no amplitude dependence on frequency
    def freqToCalibAmpl(self, freq):
        return self.ampl 

class probeLocal(doublePass):
    def __init__(self, name, cxn, context):
        super(probeLocal,self).__init__(name)
        self.selectFuncs(cxn, context)
    
    @inlineCallbacks
    def selectFuncs(self, cxn, context):
        self.server = cxn.rohdeschwarz_server
        self.context = context
        yield self.server.select_device('lattice-pc GPIB Bus - USB0::0x0AAD::0x0054::104543', context = self.context)
        self.freqRange = (190,250) #MHZ
        self.amplRange = (-145,24) #dBM
        yield self.populateInfo()
        self.freqToCalibAmpl = yield self.setupCalibration(cxn)
        
    @inlineCallbacks
    def freqFunc(self, freq = None):
        freq = yield self.server.frequency(freq, context = self.context)
        returnValue(freq) 
    
    @inlineCallbacks
    def amplFunc(self, ampl = None):
        ampl = yield self.server.amplitude(ampl, context = self.context)
        returnValue(ampl)
    
    @inlineCallbacks
    def outputFunc(self, outp= None):
        outp = yield self.server.output(outp, context = self.context)
        returnValue(outp)    
    
    @inlineCallbacks
    def setupCalibration(self, cxn):
        from scipy.interpolate import interp1d
        dv = cxn.data_vault
        yield dv.cd(['','Calibrations'],True)
        yield dv.open(62)
        calibration = yield dv.get()
        calibration = calibration.asarray
        func = interp1d(calibration[:,0],calibration[:,1],kind = 'cubic')
        returnValue(func)
        

class heatLocal(doublePass):
    def __init__(self, name, cxn, context):
        super(heatLocal,self).__init__(name)
        self.selectFuncs(cxn, context)
    
    @inlineCallbacks
    def selectFuncs(self, cxn, context):
        self.server = cxn.rohdeschwarz_server
        self.context = context
        yield self.server.select_device('lattice-pc GPIB Bus - USB0::0x0AAD::0x0054::104541', context = self.context)
        self.freqRange = (190,250) #MHZ
        self.amplRange = (-145,-13.5) #dBM
        yield self.populateInfo()
        
    @inlineCallbacks
    def freqFunc(self, freq = None):
        freq = yield self.server.frequency(freq, context = self.context)
        returnValue(freq) 
    
    @inlineCallbacks
    def amplFunc(self, ampl = None):
        ampl = yield self.server.amplitude(ampl, context = self.context)
        returnValue(ampl)
    
    @inlineCallbacks
    def outputFunc(self, outp= None):
        outp = yield self.server.output(outp, context = self.context)
        returnValue(outp)    
    
    #no calibration, that is no amplitude dependence on frequency
    def freqToCalibAmpl(self, freq):
        return self.ampl 

class doublePassServer( LabradServer ):
    name = 'Double Pass'
    onNewUpdate = Signal(SIGNALID, 'signal: double pass updated', '(ssv)')
    
    def initServer( self ):
        self.createDict()
        self.listeners = set()
        
    def createDict(self):
        self.d = {'global397':global397('global397',self.client, self.client.context()),
                  'probeLocal':probeLocal('probeLocal',self.client, self.client.context()),
                  'heatLocal':heatLocal('heatLocal',self.client, self.client.context())
                  }
        
    @setting(0, "Get Double Pass List", returns = '*s')
    def getDPList(self, c,):
        """Returns the list of available double passes"""
        return self.d.keys()
    
    @setting(1, "Select", name = 's', returns = '')
    def selectDP(self, c, name):
        """Select Double Pass in the current context"""
        if name not in self.d.keys(): raise Exception("No such double pass")
        c['doublePass'] = self.d[name]
    
    @setting(2, "Frequency", freq ='v', returns = 'v')
    def frequency(self, c, freq = None):
        """Sets the frequency of the selected double pass, returns set frequency"""
        dp = self.getDP(c)
        setfreq = yield dp.frequency(freq)
        if freq is not None: self.notifyOtherListeners(c, (dp.name,'frequency',setfreq))
        returnValue( setfreq )

    @setting(3, "Frequency Calibrated Amplitude", freq = 'v', returns = '(vv)')
    def freqCalibPower(self, c, freq):
        dp = self.getDP(c)
        (setfreq, setamplitude) = yield dp.frequencyCalibPower(freq)
        self.notifyOtherListeners(c, (dp.name,'frequency',setfreq))
        self.notifyOtherListeners(c, (dp.name,'amplitude',setamplitude))
        returnValue( (setfreq, setamplitude) )
        
    @setting(4, "Amplitude", amplitude = 'v', returns ='v')
    def amplitude(self, c, amplitude = None):
        """Sets the amplitude of the selected double pass, returns set amplitude"""
        dp = self.getDP(c)
        setamplitude = yield dp.amplitude(amplitude)
        if amplitude is not None: self.notifyOtherListeners(c, (dp.name,'amplitude',setamplitude))
        returnValue( setamplitude )
    
    @setting(5, "Amplitude Offset", offset = 'v', returns = '(vv)')
    def amplitudeOffset(self, c, offset):
        """Sets the difference between the desired power and the maximum power available from the calibration"""
        if offset > 0: raise Exception ("offset must be negatve")
        dp = self.getDP(c)
        (setoffset,setamplitude) = yield dp.amplitudeOffset(offset)
        if offset is not None: self.notifyOtherListeners(c, (dp.name,'amplitude',setamplitude))
        returnValue( (setoffset,setamplitude) )
    
    @setting(6, "Output", output = 'b', returns = 'b')
    def output(self, c, output = None):
        """Sets the output to true/false for the desired double pass"""
        dp = self.getDP(c)
        setoutput = yield dp.output(output)
        if output is not None: self.notifyOtherListeners(c, (dp.name,'output',setoutput))
        returnValue( setoutput )
    
    @setting(7, "Frequency Range", returns = '(vv)')
    def freqRange(self, c):
        """Returns the frequency range in the current context"""
        dp = self.getDP(c)
        return dp.freqRange
    
    @setting(8, "Amplitude Range", returns = '(vv)')
    def amplRange(self, c):
        """Returns the frequency range in the current context"""
        dp = self.getDP(c)
        return dp.amplRange
    
    def getDP(self, context):
        if not 'doublePass' in context.keys(): raise Exception ('Double Pass not selected')
        return context['doublePass']
    
    def notifyOtherListeners(self, context, chanInfo):
        """
        Notifies all listeners except the one in the given context
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        self.onNewUpdate(chanInfo, notified)
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(doublePassServer())
