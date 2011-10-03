#Created on Aug 12, 2011
#@author: Michael Ramm

"""
### BEGIN NODE INFO
[info]
name = NormalPMTFlow
version = 1.0
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
from twisted.internet.defer import Deferred, returnValue, inlineCallbacks, DeferredLock
from twisted.internet import reactor

SIGNALID = 331483

class NormalPMTFlow( LabradServer):
    
    name = 'NormalPMTFlow'
    onNewCount = Signal(SIGNALID, 'signal: new count', 'v')
    
    @inlineCallbacks
    def initServer(self):
        #improve on this to start in arbitrary order
        self.dv = yield self.client.data_vault
        self.n = yield self.client.normalpmtcountfpga
        self.pbox = yield self.client.paul_box
        self.trigger = yield self.client.trigger
        self.saveFolder = ['','PMT Counts']
        self.dataSetName = 'PMT Counts'
        self.dataSet = None
        self.collectTimes = {'Normal':0.100, 'Differential':0.100}
        self.lastDifferential = {'ON': 0, 'OFF': 0}
        self.currentMode = 'Normal'
        self.running = DeferredLock()
        self.requestList = []
        self.keepRunning = False
    
#    @inlineCallbacks
#    def confirmPBoxScripting(self):
#        self.script = 'DifferentialPMTCount.py'
#        self.variable = 'CountingInterval'
#        allScripts = yield self.pbox.get_available_scripts()
#        if script not in allScripts: raise Exception('Pauls Box script {} does not exist'.format(script))
#        allVariables = yield self.pbox.get_variable_list(script)
#        if variable not in allVariables[0]: raise Exception('Variable {} not found'.format(variable))
    
    @inlineCallbacks
    def makeNewDataSet(self):
        dir = self.saveFolder
        name = self.dataSetName
        yield self.dv.cd(dir, True)
        self.dataSet = yield self.dv.new(name, [('t', 'num')], [('KiloCounts/sec','866 ON','num'),('KiloCounts/sec','866 OFF','num'),('KiloCounts/sec','Differential Signal','num')])
        yield self.addParameters()
    
    @inlineCallbacks
    def addParameters(self):
        yield None
    
    @setting(0, 'Set Save Folder', folder = '*s', returns = '')
    def setSaveFolder(self,c , folder):
        yield self.dv.cd(folder, True)
        self.saveFolder = folder
    
    @setting(1, 'Start New Dataset', setName = 's', returns = '')
    def setNewDataSet(self, c, setName = None):
        """Starts new dataset, if name not provided, it will be the same"""
        if setName is not None: self.dataSetName = setName
        yield self.makeNewDataSet()
    
    @setting( 2, "Set Mode", mode = 's', returns = '' )
    def setMode(self,c, mode):
        """
        Start recording Time Resolved Counts into Data Vault
        """
        if mode not in self.collectTimes.keys(): raise('Incorrect Mode')
        if not self.keepRunning:
            self.currentMode = mode
            yield self.n.set_mode(mode)
        else:
            yield self.dostopRecording()
            self.currentMode = mode
            yield self.n.set_mode(mode)
            yield self.dorecordData()

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
        yield self.dorecordData()
    
    @inlineCallbacks
    def dorecordData(self):
        self.keepRunning = True
        yield self.n.set_collection_time(self.collectTimes[self.currentMode], self.currentMode)
        yield self.n.set_mode(self.currentMode)
        if self.currentMode == 'Differential':
            yield self._programPBOXDiff()
        if self.dataSet is None:
            yield self.makeNewDataSet()
        reactor.callLater(0, self._record)
    
    @setting(5, returns = '')
    def stopRecording(self,c):
        """
        Stop recording counts into Data Vault
        """
        yield self.dostopRecording()
    
    @inlineCallbacks
    def dostopRecording(self):
        self.keepRunning = False
        yield self.running.acquire()
        self.running.release()
        yield self._programPBOXEmpty()
        
    @setting(6, returns = 'b')
    def isRunning(self,c):
        """
        Returns whether or not currently recording
        """
        return self.keepRunning
        
    @setting(7, returns = 's')
    def currentDataSet(self,c):
        if self.dataSet is None: return ''
        name = self.dataSet[1]
        return name
    
    @setting(8, 'Set Time Length', timelength = 'v', mode = 's')
    def setTimeLength(self, c, timelength, mode = None):
        if mode is None: mode = self.currentMode
        if mode not in self.collectTimes.keys(): raise('Incorrect Mode')
        if not 0 < timelength < 5.0: raise ('Incorrect Recording Time')
        self.collectTimes[mode] = timelength
        if mode == self.currentMode:
            yield self.running.acquire()
            yield self.n.set_collection_time(timelength, mode)
            if mode == 'Differential':
                yield self._programPBOXDiff()
            self.running.release()
        else:
            yield self.n.set_collection_time(timelength, mode)
        
    @setting(9, 'Get Next Counts', type = 's', number = 'w', average = 'b', returns = ['*v', 'v'])
    def getNextCounts(self, c, type, number, average = False):
        """
        Acquires next number of counts, where type can be 'ON' or 'OFF' or 'DIFF'
        Average is optionally True if the counts should be averaged
        
        Note in differential mode, Diff counts get updates every time, but ON and OFF
        get updated every 2 times.
        """
        if type not in ['ON', 'OFF','DIFF']: raise('Incorrect type')
        if type in ['OFF','DIFF'] and self.currentMode == 'Normal':raise('in the wrong mode to process this request')
        if not 0 < number < 1000: raise('Incorrect Number')
        if not self.keepRunning: raise('Not currently recording')
        d = Deferred()
        self.requestList.append(self.readingRequest(d, type, number))
        data = yield d
        if average:
            data = sum(data) / len(data)
        returnValue(data)
    
    @setting(10, 'Get Time Length', returns = 'v')
    def getMode(self, c):
        """
        Returns the current timelength of in the current mode
        """
        return self.collectTimes[self.currentMode]
    
    @inlineCallbacks
    def _programPBOXDiff(self):
        yield self.pbox.send_command('DifferentialPMTCount.py',[['FLOAT','CountingInterval',str(10**6 * self.collectTimes['Differential'])]])
        yield self.trigger.trigger('PaulBox')
    
    @inlineCallbacks
    def _programPBOXEmpty(self):
        yield self.pbox.send_command('emptySequence.py',[['FLOAT','nothing','0']])
        yield self.trigger.trigger('PaulBox')
        
    class readingRequest():
        def __init__(self, d, type, count):
            self.d = d
            self.count = count
            self.type = type
            self.data = []
    
    def processRequests(self, data):
        for dataPoint in data:
            for req in self.requestList:
                if dataPoint[1] != 0 and req.type == 'ON':
                    req.data.append(dataPoint[1])
                    if len(req.data) == req.count:
                        req.d.callback(req.data)
                if dataPoint[2] != 0 and req.type == 'OFF':
                    req.data.append(dataPoint[1])
                    if len(req.data) == req.count:
                        req.d.callback(req.data)
                if dataPoint[3] != 0 and req.type == 'DIFF':
                    req.data.append(dataPoint[1])
                    if len(req.data) == req.count:
                        req.d.callback(req.data)
                        
    @inlineCallbacks
    def _record(self):
        yield self.running.acquire()
        if self.keepRunning:
            rawdata = yield self.n.get_all_counts()
            if len(rawdata) != 0:
                if self.currentMode == 'Normal':
                    toDataVault = [ [elem[2], elem[0], 0, 0] for elem in rawdata] # converting to format [time, normal count, 0 , 0]
                elif self.currentMode =='Differential':
                    toDataVault = self.convertDifferential(rawdata)
                self.processRequests(toDataVault)
                self.processSignals(toDataVault)
                yield self.dv.add(toDataVault)
            self.running.release()
            delayTime = self.collectTimes[self.currentMode]/2 #set to half the collection time no to miss anythign
            reactor.callLater(delayTime,self._record)
        else:
            self.running.release()
    
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
            totalData.append( [ dataPoint[2], self.lastDifferential['ON'], self.lastDifferential['OFF'], diff ] )
        return totalData
            
if __name__ == "__main__":
    from labrad import util
    util.runServer( NormalPMTFlow() )