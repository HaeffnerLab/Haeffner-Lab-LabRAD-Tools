#Created on Aug 11, 2011
#Last Modified on Sep 14, 2011
#@author: Michael Ramm

"""
### BEGIN NODE INFO
[info]
name = dataProcessor
version = 1.0
description = 
instancename = dataProcessor

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from twisted.internet.defer import returnValue
from labrad.server import LabradServer, setting
from twisted.internet.threads import deferToThread
#from timeResolvedFullFFT import timeResolvedFullFFT
from timeResolvedBinning import timeResolvedBinning

class dataProcessor( LabradServer ):
    """
    Server for Processing Data
    """
    name = 'dataProcessor'
    def initServer(self):
        self.setupProcessInfo()  
    
    def setupProcessInfo(self):
        """
        Sets up the information about all available tasks
        """
        self.processDict = {}
        importedProcesses = [timeResolvedBinning]
        for process in importedProcesses:
            self.processDict[process.name] = process
        
    @setting(0, 'Get Available Processes', returns = '*s')
    def getAvailableProcesses(self, c):
        """
        Returns the list of names with processes available for running.
        """
        return self.processDict.keys()
    
    @setting(1, 'Get Inputs Required', processName = 's', returns = '*s')
    def getRequiredInputs(self, c, processName):
        """
        Returns the list of inputs for the given process.
        """
        if processName not in self.processDict.keys(): raise Exception('Process Name Not Found')
        return self.processDict[processName].inputsRequired
    
    @setting(2, 'Get Inputs Optional', processName = 's', returns = '')
    def getOptionalInputs(self, c, processName):
        """
        Returns the list of optional inputs for the given process in the form (name, value)
        """
        if processName not in self.processDict.keys(): raise Exception('Process Name Not Found')
        return self.processDict[processName].inputsOptional
    
    @setting(3, 'Set Inputs', processName = 's',inputs = ['*(sv)','*(ss)'], returns = '')
    def setInputs(self, c, processName, inputs):
        """
        For the current context, sets the inputs for processName for future executions.
        """
        c['inputs'] = {processName : inputs }
               
    @setting(4, 'New Process', processName = 's', returns = '')
    def newProcess(self, c, processName):
        """
        Sets up the execution of the specified process. All inputs must be set prior.
        """
        if processName not in self.processDict.keys(): raise Exception('Process Name Not Found')
        if processName not in c['inputs'].keys():
            inputs = None
        else:
            inputs = c['inputs'][processName]
        process = self.processDict[processName]
        instance = process(inputs)
        c['processInstances'][processName] = instance
        
    @setting(5, 'Process New Data', processName = 's', newdata = '?', returns = '')
    def processNewData(self, c, processName, newdata):
        """
        Starts execution the specified process.  to execution to
        set any required inputs for the process.
        """
        if processName not in c['processInstances'].keys(): raise Exception('Process does not exist')
        instance =  c['processInstances'][processName]
        yield deferToThread(instance.processNewData, newdata)
    
    @setting(6, 'Get Result', processName = 's', returns = '?')
    def getResult(self, c, processName):
        if processName not in c['processInstances'].keys(): raise Exception('Process does not exist')
        instance =  c['processInstances'][processName]
        result = yield deferToThread(instance.getResult)
        returnValue( result )
        
    #@setting closeProcess (if necessary)
    #expireContext (if necessary)
    
    def initContext(self, c):
        c['inputs'] = {}
        c['processInstances'] = {}
            
if __name__ == "__main__":
    from labrad import util
    util.runServer( dataProcessor() )