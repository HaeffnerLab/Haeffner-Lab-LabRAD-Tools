from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
from twisted.internet.defer import returnValue
from labrad.server import Signal
import numpy

class TPSserver( SerialDeviceServer ):
    """Controls TPS 2000 and 1000 series Oscilloscope"""

    name = 'TPS Server'
    regKey = 'TPSscope'
    port = None
    serNode = 'lattic-imaging'
    timeout = 1.0

    @inlineCallbacks
    def initServer( self ):
        self.createDict()
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        try:
            serStr = yield self.findSerial( self.serNode )
            self.initSerial( serStr, port )
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise
        yield self.populateDict()        

    def createDict(self):
        d = {}
        d['X0'] = None #trigger position
        d['Xinc'] = None #time increment
        d['Ymulti'] = None #Voltage increment
        d['Yoff'] = None #Voltage offset
        d['Y0'] = None # position of 0V
        d['Datalength'] = None #number of datapoints
        d['readystate'] = None # boolean 1=ready to trigger, 0= triggered, waiting for next command
        self.tpsDict = d

    @inlineCallbacks
    def populateDict(self):
        X0 = yield self._readX0() 
        Xinc = yield self._readXinc()
        Ymulti = yield self._readYmulti()
        Yoff = yield self._readYoff()
        Y0 = yield self._readY0()
        
        Datalength = yield self._readdatalength()
        Datasource = yield self._readdatasource()
        self.tpsDict['X0'] = float(X0) 
        self.tpsDict['Xinc'] = float(Xinc)
        self.tpsDict['Ymulti'] = float(Ymulti)
        self.tpsDict['Yoff'] = float(Yoff)
        self.tpsDict['Y0'] = float(Y0)
        self.tpsDict['Datalength'] = float(Datalength)
        self.tpsDict['Datasource'] = Datasource
        print X0
        print Xinc
        print Y0
        print Ymulti
        print Yoff
        print Datalength
        
    @setting(1, "Identify", returns='s')
    def Identify(self, c):
        '''Ask instrument to identify itself'''
        command = self.IdenStr()
        yield self.ser.write_line(command)
        answer = yield self.ser.readline()
        returnValue(answer)

    @setting(2, "readY0", returns='v')
    def readY0(self,c):
        return self._readY0()

    @setting(3, "setchannel",channelnbr='i' , returns='')  #Sets new channel and gets Y scaling for that channel
    def setchannel(self,c,channelnbr):
        '''Set the Channel you want to take data from'''
        channel=str(channelnbr)
        command1=self.setdatasourcestr(channel)
        yield self.ser.write_line(command1)
        command2=self.getdatasourcestr()
        yield self.ser.write_line(command2)
        answer= yield self.ser.readline()
        wantch='CH'+channel
        print answer
        if answer != wantch: raise Exception('Channel not properbly set. Make sure channel you set exists')
        Ymulti = yield self._readYmulti()
        Yoff = yield self._readYoff()
        Y0 = yield self._readY0()        
        self.tpsDict['Ymulti'] = float(Ymulti)
        self.tpsDict['Yoff'] = float(Yoff)
        self.tpsDict['Y0'] = float(Y0)

    @setting(4, "getcurve", returns='*2v')
    def getcurve(self,c):
        yield self.populateDict()
        datastr = yield self._readData()
        dataarray = numpy.fromstring(datastr, sep=',')
        voltarray =(dataarray-self.tpsDict['Yoff'])*self.tpsDict['Ymulti']+self.tpsDict['Y0']
        tarray=[]
        t0=self.tpsDict['X0']
        dt=self.tpsDict['Xinc']
        length=self.tpsDict['Datalength']
        tf=t0+length*dt
        tarr = numpy.arange(t0,tf,dt)
        #for i in range(length):
        #    tstr=t0+i*dt
         #   tarray.append(tstr)
        intarr = numpy.vstack((tarr,voltarray))
        answer = intarr.transpose()
        returnValue(answer)

    @inlineCallbacks
    def _createTarray(self):    
        tarray=[]
        t0=self.tpsDict['X0']
        dt=self.tpsDict['Xinc']
        length=self.tpsDict['Datalength']
        for i in range(length):
            tstr=t0+i*dt
            tarray.append(tstr)
        answer=tarray
        returnValue(answer)
            
    @inlineCallbacks
    def _readX0(self):
        command=self.getX0str()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)


    @inlineCallbacks
    def _readXinc(self):
        command=self.getXincstr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)
        
    @inlineCallbacks
    def _readYmulti(self):
        command=self.getYmultistr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)

    @inlineCallbacks
    def _readYoff(self):
        command=self.getYoffstr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)

    @inlineCallbacks
    def _readY0(self):
        command=self.getY0str()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)

    @inlineCallbacks
    def _readdatalength(self):
        command=self.getdatalengthstr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)

    @inlineCallbacks
    def _readready(self):
        command=self.getreadystr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)

    @inlineCallbacks
    def _readData(self):
        command=self.getDatastr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)



    @inlineCallbacks
    def _readdatasource(self):
        command = self.getdatasourcestr()
        yield self.ser.write_line(command)        
        answer=yield self.ser.readline()
        returnValue(answer)        

        
    def getdatasourcestr(self):
        return 'DATa:SOUrce?'

    def setdatasourcestr(self, channel): #sets source for all queries to channel if channel dependend
        command = 'DATa:SOUrce CH' + channel
        return command
        
    def IdenStr(self):
        return '*IDN?'

    def encASCIIstr(self): #sets data encoding to ascii
        return 'DATa:ENCdg ASCi'

    def getX0str(self): #gets trigger time
        return 'WFMPre:XZEro?'

    def getXincstr(self): #gets time step
        return 'WFMPre:XINc?'

    def setDatawidthstr(self): #Sets datawidth to 1
        return 'DATa:WIDth 1'

    def getYmultistr(self):
        return 'WFMPre:YMUlt?'

    def getYoffstr(self): #get Yoffset
        return 'WFMPre:YOFf?'

    def getY0str(self): #get Y0
        return 'WFMPre:YZEro?'

    def getdatalengthstr(self): #gets the number of elements sent by oscilloscope
        return 'DATa:STOP?'

    def setsingletriggerstr(self): #stops aqu. after single trigger
        return 'ACQuire:STOPAfter SEQuence'

    def getreadystr(self): #asks if Osc is ready to trigger
        return 'ACQuire:STATE 1'

    def setreadystr(self): #turns on aquisition
        return 'ACQuire:STATE?'

    def getDatastr(self): #gets current displayed waveform data
        return 'CURVe?'

        
if __name__ == "__main__":
    from labrad import util
    util.runServer(TPSserver())
