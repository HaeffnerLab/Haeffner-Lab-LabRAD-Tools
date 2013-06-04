#Created on Aug 12, 2011
#@author: Michael Ramm

"""
### BEGIN NODE INFO
[info]
name = NormalPMTFlow
version = 1.32
description = 
instancename = NormalPMTFlow

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from labrad import types as T
from twisted.internet.defer import Deferred, returnValue, inlineCallbacks
from twisted.internet.task import LoopingCall
import time

SIGNALID = 331483

class NormalPMTFlow( LabradServer):
    
    name = 'NormalPMTFlow'
    onNewCount = Signal(SIGNALID, 'signal: new count', 'v')
    onNewSetting = Signal(SIGNALID+1, 'signal: new setting', '(ss)')
    
    @inlineCallbacks
    def initServer(self):
        self.saveFolder = ['','PMT Counts']
        self.dataSetName = 'PMT Counts'
        self.modes = ['Normal', 'Differential']
        self.collection_period= T.Value(0.100,'s')
        self.lastDifferential = {'ON': 0, 'OFF': 0}
        self.currentMode = 'Normal'
        self.dv = None
        self.pulser = None
        self.collectTimeRange = None
        self.openDataSet = None
        self.recordingInterrupted = False
        self.requestList = []
        self.listeners = set()
        self.recording = LoopingCall(self._record)
        yield self.connect_data_vault()
        yield self.connect_pulser()
        yield self.setupListeners()
    
    @inlineCallbacks
    def setupListeners(self):
        yield self.client.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.client.manager.subscribe_to_named_message('Server Disconnect', 9898989+1, True)
        yield self.client.manager.addListener(listener = self.followServerConnect, source = None, ID = 9898989)
        yield self.client.manager.addListener(listener = self.followServerDisconnect, source = None, ID = 9898989+1)
    
    @inlineCallbacks
    def followServerConnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Pulser':
            yield self.connect_pulser()
        elif serverName == 'Data Vault':
            yield self.connect_data_vault()
    
    @inlineCallbacks
    def followServerDisconnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Pulser':
            yield self.disconnect_pulser()
        elif serverName == 'Data Vault':
            yield self.disconnect_data_vault()  
       
    @inlineCallbacks
    def connect_data_vault(self):
        try:
            #reconnect to data vault and navigate to the directory
            self.dv = yield self.client.data_vault
            yield self.dv.cd(self.saveFolder, True)    
            if self.openDataSet is not None:
                self.openDataSet = yield self.makeNewDataSet(self.saveFolder, self.dataSetName)        
                self.onNewSetting(('dataset', self.openDataSet))
            print 'Connected: Data Vault'
        except AttributeError:
            self.dv = None
            print 'Not Connected: Data Vault'
    
    @inlineCallbacks
    def disconnect_data_vault(self):
        print 'Not Connected: Data Vault'
        self.dv = None
        yield None
    
    @inlineCallbacks
    def connect_pulser(self):
        try:
            self.pulser = yield self.client.pulser
            self.collectTimeRange = yield self.pulser.get_collection_time()
            if self.recordingInterrupted:
                yield self.dorecordData()
                self.onNewSetting(('state', 'on'))
                self.recordingInterrupted = False
            print 'Connected: Pulser'
        except AttributeError:
            self.pulser = None
            print 'Not Connected: Pulser'
    
    @inlineCallbacks
    def disconnect_pulser(self):
        print 'Not Connected: Pulser'
        self.pulser = None
        if self.recording.running:
            yield self.recording.stop()
            self.onNewSetting(('state', 'off'))
            self.recordingInterrupted = True
            
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)
  
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified  
       
    @inlineCallbacks
    def makeNewDataSet(self, folder, name):
        yield self.dv.cd(folder, True)
        newSet = yield self.dv.new(name, [('t', 'num')], [('KiloCounts/sec','866 ON','num'),('KiloCounts/sec','866 OFF','num'),('KiloCounts/sec','Differential Signal','num')])
        self.startTime = time.time()
        yield self.addParameters(self.startTime)
        name = newSet[1]
        returnValue(name)
    
    @inlineCallbacks
    def addParameters(self, start):
        yield self.dv.add_parameter("Window", ["PMT Counts"])
        yield self.dv.add_parameter('plotLive',True)
        yield self.dv.add_parameter('startTime',start)
    
    @setting(0, 'Set Save Folder', folder = '*s', returns = '')
    def setSaveFolder(self,c , folder):
        yield self.dv.cd(folder, True)
        self.saveFolder = folder
    
    @setting(1, 'Start New Dataset', setName = 's', returns = 's')
    def setNewDataSet(self, c, setName = None):
        """Starts new dataset, if name not provided, it will be the same"""
        if setName is not None: self.dataSetName = setName
        self.openDataSet = yield self.makeNewDataSet(self.saveFolder, self.dataSetName)
        otherListeners = self.getOtherListeners(c)
        self.onNewSetting(('dataset', self.openDataSet), otherListeners)
        returnValue(self.openDataSet)
    
    @setting( 2, "Set Mode", mode = 's', returns = '' )
    def setMode(self,c, mode):
        """
        Start recording Time Resolved Counts into Data Vault
        """
        if mode not in self.modes: raise Exception('Incorrect Mode')
        if not self.recording.running:
            self.currentMode = mode
            yield self.pulser.set_mode(mode)
        else:
            yield self.dostopRecording()
            self.currentMode = mode
            yield self.dorecordData()
        otherListeners = self.getOtherListeners(c)      
        self.onNewSetting(('mode', mode), otherListeners)

    @setting(3, 'getCurrentMode', returns = 's')
    def getCurrentMode(self, c):
        """
        Returns the currently running mode
        """
        return self.currentMode
    
    @setting(4, 'Record Data', returns = '')
    def recordData(self, c):
        """
        Starts recording data of the current PMT mode into datavault
        """
        setname = yield self.dorecordData()
        otherListeners = self.getOtherListeners(c)
        if setname is not None:
            setname = setname[1]
            self.onNewSetting(('dataset', setname), otherListeners)
        self.onNewSetting(('state', 'on'), otherListeners)
    
    @inlineCallbacks
    def dorecordData(self):
        #begins the process of data record
        #sets the collection time and mode, programs the pulser if necessary and opens the dataset if necessasry
        #then starts the recording loop
        newSet = None
        self.keepRunning = True
        yield self.pulser.set_collection_time(self.collection_period, self.currentMode)
        yield self.pulser.set_mode(self.currentMode)
        if self.currentMode == 'Differential':
            yield self._programPulserDiff()
        if self.openDataSet is None:
            self.openDataSet = yield self.makeNewDataSet(self.saveFolder, self.dataSetName)
        self.recording.start(self.collection_period['s']/2.0)
        returnValue(newSet)
        
    @setting(5, returns = '')
    def stopRecording(self,c):
        """
        Stop recording counts into Data Vault
        """
        yield self.dostopRecording()
        otherListeners = self.getOtherListeners(c)
        self.onNewSetting(('state', 'off'), otherListeners)
    
    @inlineCallbacks
    def dostopRecording(self):
        yield self.recording.stop()
        if self.currentMode == 'Differential':
            yield self._stopPulserDiff()
            
    @setting(6, returns = 'b')
    def isRunning(self,c):
        """
        Returns whether or not currently recording
        """
        return self.recording.running
        
    @setting(7, returns = 's')
    def currentDataSet(self,c):
        if self.openDataSet is None: return ''
        return self.openDataSet
    
    @setting(8, 'Set Time Length', timelength = 'v[s]')
    def setTimeLength(self, c, timelength):
        """Sets the time length for the current mode"""
        mode = self.currentMode
        if not self.collectTimeRange[0] <= timelength['s'] <= self.collectTimeRange[1]: raise Exception ('Incorrect Recording Time')
        self.collection_period = timelength
        initrunning = self.recording.running #if recording when the call is made, need to stop and restart
        if initrunning:
            yield self.recording.stop()
        yield self.pulser.set_collection_time(timelength['s'], mode)
        if initrunning:
            if mode == 'Differential':
                yield self._stopPulserDiff()
                yield self._programPulserDiff()
            self.recording.start(timelength['s']/2.0)
        otherListeners = self.getOtherListeners(c)      
        self.onNewSetting(('timelength', str(timelength['s'])), otherListeners)
    
    @setting(9, 'Get Next Counts', kind = 's', number = 'w', average = 'b', returns = ['*v', 'v'])
    def getNextCounts(self, c, kind, number, average = False):
        """
        Acquires next number of counts, where type can be 'ON' or 'OFF' or 'DIFF'
        Average is optionally True if the counts should be averaged
        
        Note in differential mode, Diff counts get updates every time, but ON and OFF
        get updated every 2 times.
        """
        if kind not in ['ON', 'OFF','DIFF']: raise Exception('Incorrect type')
        if kind in ['OFF','DIFF'] and self.currentMode == 'Normal':raise Exception('in the wrong mode to process this request')
        if not 0 < number < 1000: raise Exception('Incorrect Number')
        if not self.recording.running: raise Exception('Not currently recording')
        d = Deferred()
        self.requestList.append(self.readingRequest(d, kind, number))
        data = yield d
        if average:
            data = sum(data) / len(data)
        returnValue(data)
    
    @setting(10, 'Get Time Length', returns = 'v')
    def getMode(self, c):
        """
        Returns the current timelength of in the current mode
        """
        return self.collection_period

    @setting(11, 'Get Time Length Range', returns = '(vv)')
    def get_time_length_range(self, c):
        if self.collectTimeRange is not None:
            return self.collectTimeRange
        else:
            raise Exception("Not available because Pulser Server is not available")
    
    @inlineCallbacks
    def _programPulserDiff(self):
        yield self.pulser.new_sequence()
        yield self.pulser.add_ttl_pulse('DiffCountTrigger', T.Value(0.0,'us'), T.Value(10.0,'us'))
        yield self.pulser.add_ttl_pulse('DiffCountTrigger', self.collection_period, T.Value(10.0,'us'))
        yield self.pulser.add_ttl_pulse('866DP', T.Value(0.0,'us'), self.collection_period)
        yield self.pulser.add_ttl_pulse('Internal866', T.Value(0.0,'us'), self.collection_period)
        yield self.pulser.extend_sequence_length(2 * self.collection_period)
        yield self.pulser.program_sequence()
        yield self.pulser.start_infinite()
    
    @inlineCallbacks
    def _stopPulserDiff(self):
        yield self.pulser.complete_infinite_iteration()
        yield self.pulser.wait_sequence_done()
        yield self.pulser.stop_sequence()
        
    class readingRequest():
        def __init__(self, d, kind, count):
            self.d = d
            self.count = count
            self.kind = kind
            self.data = []
        
        def is_fulfilled(self):
            return len(self.data) == self.count
    
    def processRequests(self, data):
        if not len(self.requestList): return
        for dataPoint in data:
            for item,req in enumerate(self.requestList):
                if dataPoint[1] != 0 and req.kind == 'ON':
                    req.data.append(dataPoint[1])
                if dataPoint[2] != 0 and req.kind == 'OFF':
                    req.data.append(dataPoint[2])
                if dataPoint[3] != 0 and req.kind == 'DIFF':
                    req.data.append(dataPoint[3])
                if req.is_fulfilled():
                    req.d.callback(req.data)
                    del(self.requestList[item])
                    
    @inlineCallbacks
    def _record(self):
        try:
            rawdata = yield self.pulser.get_pmt_counts()
        except:
            print 'Not Able to Get PMT Counts'
            rawdata = []
        if len(rawdata) != 0:
            if self.currentMode == 'Normal':
                toDataVault = [ [elem[2] - self.startTime, elem[0], 0, 0] for elem in rawdata] # converting to format [time, normal count, 0 , 0]
            elif self.currentMode =='Differential':
                toDataVault = self.convertDifferential(rawdata)
            self.processRequests(toDataVault) #if we have any requests, process them
            self.processSignals(toDataVault)
            try:
                yield self.dv.add(toDataVault)
            except:
                print 'Not Able to Save To Data Vault'
    
    def processSignals(self, data):
        lastPt = data[-1]
        NormalCount = lastPt[1]
        self.onNewCount(NormalCount)
    
    def convertDifferential(self, rawdata):
        totalData = []
        for dataPoint in rawdata:
            t = str(dataPoint[1])
            self.lastDifferential[t] = float(dataPoint[0])
            diff = self.lastDifferential['ON'] - self.lastDifferential['OFF']
            totalData.append( [ dataPoint[2] - self.startTime, self.lastDifferential['ON'], self.lastDifferential['OFF'], diff ] )
        return totalData

if __name__ == "__main__":
    from labrad import util
    util.runServer( NormalPMTFlow() )