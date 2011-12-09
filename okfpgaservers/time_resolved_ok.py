#Created on Aug 08, 2011
#@author: Michael Ramm, Haeffner Lab
#Thanks for code ideas from Quanta Lab, MIT
'''
### BEGIN NODE INFO
[info]
name = TimeResolvedFPGA
version = 2.0
description = 
instancename = TimeResolvedFPGA

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

import ok
from labrad.server import LabradServer, setting
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet.threads import deferToThread
import os
import numpy
import time

okDeviceID = 'TimeResolvedFPGA'
DefaultTimeLength = 0.1 #seconds
devicePollingPeriod = 10
MINBUF,MAXBUF = [1024, 16776192] #range of allowed buffer lengths
timeResolution = 5.0*10**-9 #seconds

class TimeResolvedFPGA(LabradServer):
    name = 'TimeResolvedFPGA'
    
    def initServer(self):
        self.inRequest = False
        self.singleReadingDeferred = None
        self.timelength = DefaultTimeLength
        self.connectOKBoard()
    
    def connectOKBoard(self):
        self.xem = None
        fp = ok.FrontPanel()
        module_count = fp.GetDeviceCount()
        print "Found {} unused modules".format(module_count)
        for i in range(module_count):
            serial = fp.GetDeviceListSerial(i)
            tmp = ok.FrontPanel()
            tmp.OpenBySerial(serial)
            id = tmp.GetDeviceID()
            if id == okDeviceID:
                self.xem = tmp
                print 'Connected to {}'.format(id)
                self.programOKBoard(self.xem)
                return
        print 'Not found {}'.format(okDeviceID)
        print 'Will try again in {} seconds'.format(devicePollingPeriod)
        reactor.callLater(devicePollingPeriod, self.connectOKBoard)
    
    def programOKBoard(self, xem):
        print 'Programming FPGA'
        basepath = os.environ.get('LABRADPATH',None)
        if not basepath:
            raise Exception('Please set your LABRADPATH environment variable')
        path = os.path.join(basepath,'lattice/okfpgaservers/led.bit')
        prog = xem.ConfigureFPGA(path)
        if prog: raise("Not able to program FPGA")
        pll = ok.PLL22150()
        xem.GetEepromPLL22150Configuration(pll)
        pll.SetDiv1(pll.DivSrc_VCO,4)
        xem.SetPLL22150Configuration(pll)
    
    @setting(0, "Perform Time Resolved Measurement", timelength = 'v[s]', returns = '')
    def performSingleReading(self, c, timelength = None):
        """
        Commands to OK board to get ready to perform a single measurement
        The result can then be retrieved with getSingleResult()
        """
        if self.xem is None: raise('Board not connected')
        if self.inRequest: raise('Board busy performing a measurement')
        self.inRequest = True
        if timelength is None: timelength = self.timelength
        buflength = self.findBufLength(timelength)
        self.singleReadingDeferred = Deferred()
        yield deferToThread(self._resetBoard)
        reactor.callLater(0, self.doSingleReading, buflength)
        #delay to make sure the previous command got to the  ReadFromBlockPipeOut line and FPGA is ready to be triggered
        yield deferToThread(time.sleep, 0.020) 
    
    @inlineCallbacks
    def doSingleReading(self, buflength):
        yield deferToThread(self._singleReading, buflength)

    def _resetBoard(self):
        self.xem.ActivateTriggerIn(0x40,0) #reset the board and FIFO
        
    def _singleReading(self, buflength):
        #xem API does not allow for timeouts, so the only way to get out of ReadFromBlockPipeOut is to have the function complete
        buf = '\x00'*buflength
        self.xem.ReadFromBlockPipeOut(0xa0,1024,buf)
        self.inRequest = False
        self.singleReadingDeferred.callback(buf)
    
    @staticmethod
    def findBufLength(timelength):
        """
        Converts time length in seconds to length of the buffer needed to request that much data
        Buffer is rounded to 1024 for optimal data transfer rate.
        """
        return int(timelength / (8 * timeResolution )) / 1024 * 1024
    
    @staticmethod
    def getOptimalTiming():
        """
        Return computationally preferable measurement times, that correspond to future arrays that are powers of 2 and are easy to FFT.
        """
        powers = numpy.array([2**p for p in range(10,25)])
        times = powers * 8 * timeResolution
        return times
        
    @setting(1, 'Get Result of Measurement', returns = '*v')
    def getSingleResult(self, c):
        """
        Acquires the result of a single reading requested earlier
        The output are the time tags of arriving photons
        """
        if self.singleReadingDeferred is None: raise "Single reading was not previously requested"
        raw = yield self.singleReadingDeferred
        self.singleReadingDeferred = None
        data = numpy.fromstring(raw, dtype = numpy.uint16)
        timetags = data.nonzero()[0]*timeResolution * 16
        del(data)
        returnValue(timetags)
        
    @setting(2, 'Set Time Length', timelength = 'v[s]', returns = '')
    def setTimeLength(self, c, timelength):
        """
        Sets the default time length for measurements in seconds
        """
        timelength = timelength['s']
        buflength = self.findBufLength(timelength)
        if not MINBUF <= buflength <= MAXBUF: raise('Incorrect timelength: buffer length out of bounds')
        self.timelength = timelength
    
    @setting(3, 'Get Optimal Time Lengths', returns = '*v')
    def optimalTL(self, c):
        """
        Returns Optimal Time Lengths that will be easy to process for FFT
        """
        return self.getOptimalTiming()
    
    @setting(4, 'Get Resolution', returns = 'v')
    def getResolution(self,c ):
        return timeResolution
  
if __name__ == "__main__":
    from labrad import util
    util.runServer( TimeResolvedFPGA() )