# -*- coding: utf-8 -*-


"""
### BEGIN NODE INFO
[info]
name = Tektronix TDS Server
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
import numpy
from numpy import *


class TektronixTDS2014CWrapper(GPIBDeviceWrapper):
    @inlineCallbacks
    def getdatassourcestr(self):
        result = yield self.query('DATa:SOUrce?')
        returnValue(result)

    @inlineCallbacks
    def setdatasourcestr(self, channel): #sets source for all queries to channel if channel dependend
        result = yield self.write('DATa:SOUrce CH' + str(channel))
        returnValue(result)

    @inlineCallbacks
    def IdenStr(self):
        result = yield self.query('*IDN?')
        returnValue(result)

    @inlineCallbacks
    def encASCIIstr(self): #sets data encoding to ascii
        result = yield self.write('DATa:ENCdg ASCi')
        returnValue(result)

    @inlineCallbacks
    def getX0str(self): #gets trigger time
        result = yield self.query('WFMPre:XZEro?')
        returnValue(result)

    @inlineCallbacks
    def getXincstr(self): #gets time step
        result = yield self.query('WFMPre:XINcr?')
        returnValue(result)

    @inlineCallbacks
    def setDatawidthstr(self): #Sets datawidth to 1
        result = yield self.query('DATa:WIDth 1')
        returnValue(result)

    @inlineCallbacks
    def getYmultistr(self):
        result = yield self.query('WFMPre:YMUlt?')
        returnValue(result)

    @inlineCallbacks
    def getYoffstr(self): #get Yoffset
        result = yield self.query('WFMPre:YOFf?')
        returnValue(result)

    @inlineCallbacks
    def getY0str(self): #get Y0
        result = yield self.query('WFMPre:YZEro?')
        returnValue(result)

    @inlineCallbacks
    def getdatalengthstr(self): #gets the number of elements sent by oscilloscope
        result = yield self.query('DATa:STOP?')
        returnValue(result)

    @inlineCallbacks
    def setsingletriggerstr(self): #stops aqu. after single trigger
        result = yield self.query('ACQuire:STOPAfter SEQuence')
        returnValue(result)

    @inlineCallbacks
    def getreadystr(self): #asks if Osc is ready to trigger
        result = yield self.query('ACQuire:STATE 1')
        returnValue(result)

    @inlineCallbacks
    def setreadystr(self): #turns on aquisition
        result = yield self.write('ACQuire:STATE?')
        returnValue(result)

    @inlineCallbacks
    def getDatastr(self): #gets current displayed waveform data
        result = yield self.query('CURVe?')
        returnValue(result)


class TektronixTDSServer(GPIBManagedServer):
    #Provides basic control for Tektronix 2014C Oscilloscope
    name = 'TektronixTDS Server'
    deviceName = 'TEKTRONIX TDS 2014C'
    deviceWrapper = TektronixTDS2014CWrapper

    
    def createDict(self):
        d = {}
        d['X0'] = None #trigger position
        d['Xinc'] = None #time increment
        d['Ymulti'] = None #Voltage increment
        d['Yoff'] = None #Voltage offset
        d['Y0'] = None # position of 0V
        d['Datalength'] = None #number of datapoints
        d['readystate'] = None # boolean 1=ready to trigger, 0= triggered, waiting for next command
        self.tdsDict = d
        
    @inlineCallbacks
    def populateDict(self, c):
        X0 = yield self._readX0(c) 
        Xinc = yield self._readXinc(c)
        Ymulti = yield self._readYmulti(c)
        Yoff = yield self._readYoff(c)
        Y0 = yield self._readY0(c)        
        Datalength = yield self._readdatalength(c)
        Datasource = yield self._readdatasource(c)

        self.createDict()

        self.tdsDict['X0'] = float(X0) 
        self.tdsDict['Xinc'] = float(Xinc)
        self.tdsDict['Ymulti'] = float(Ymulti)
        self.tdsDict['Yoff'] = float(Yoff)
        self.tdsDict['Y0'] = float(Y0)
        self.tdsDict['Datalength'] = int(Datalength) 
        self.tdsDict['Datasource'] = Datasource  


    @setting(101, 'Identify', returns='s')
    def Identify(self, c):
        '''Ask current instrument to identify itself'''
        dev = self.selectedDevice(c)
        answer = yield dev.IdenStr()
        returnValue(answer)


    @setting(102, 'readY0', returns='v')
    def readY0(self,c):        
        dev = self.selectedDevice(c)
        answer = yield dev.getY0str()
        returnValue(answer)
       
       
    @setting(103, 'setchannel',channelnbr='i' , returns='')
    def setchannel(self,c,channelnbr):
        '''Set the Channel you want to take data from'''
        dev = self.selectedDevice(c)
        answer = yield dev.setdatasourcestr(channelnbr)
        returnValue(answer)
       
       
    @setting(104, 'getcurve', returns='*2v')  # ??? why *2v ?
    def getcurve(self, c):
        yield self.populateDict(c)
        dev = self.selectedDevice(c)
        dev.encASCIIstr()
        datastr = yield self._readData(c)
        dataarray = numpy.fromstring(datastr, sep=',')
        voltarray =(dataarray-self.tdsDict['Yoff'])*self.tdsDict['Ymulti']+self.tdsDict['Y0']
        t0=self.tdsDict['X0']
        dt=self.tdsDict['Xinc']
        length=self.tdsDict['Datalength']        
        tarray = t0 + dt*array(range(length))        
        intarr = numpy.vstack((tarray,voltarray))
        answer = intarr.transpose()
        returnValue(answer)


    @inlineCallbacks
    def _readX0(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getX0str()
        returnValue(answer)        

    @inlineCallbacks
    def _readXinc(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getXincstr()
        returnValue(answer)        
        
    @inlineCallbacks
    def _readYmulti(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getYmultistr()
        returnValue(answer)        
        
    @inlineCallbacks
    def _readYoff(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getYoffstr()
        returnValue(answer)        

    @inlineCallbacks
    def _readdatasource(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getdatassourcestr()        
        returnValue(answer)

    @inlineCallbacks
    def _readY0(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getY0str()
        returnValue(answer)

    @inlineCallbacks
    def _readdatalength(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.getdatalengthstr()        
        returnValue(answer)
        
    @inlineCallbacks
    def _readready(self, c):
        dev = self.selectedDevice(c)
        answer = yield dev.setreadystr()        
        returnValue(answer) 

    @inlineCallbacks
    def _readData(self, c):
       dev = self.selectedDevice(c)
       answer = yield dev.getDatastr()        
       returnValue(answer)        


__server__ = TektronixTDSServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
