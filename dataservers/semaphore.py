"""
### BEGIN NODE INFO
[info]
name = Semaphore
version = 1.1
description = 
instancename = Semaphore

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

class Semaphore(LabradServer):
    """Houses the Blocking Function"""
    name = "Semaphore"
    registryDirectory = ['','Servers', 'Semaphore']
    onParameterChange = Signal(222222, 'signal: parameter change', ['(*s, *v)', '(*s, b)', '(*s, s)', '(*s, v)', '*s*(sv)', '(*s, *s)','?'])

    @inlineCallbacks
    def initServer(self):
        self.listeners = set()  
        self.parametersDict = None
        yield self.loadDictionary()
    
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
    def loadDictionary(self):
        self.parametersDict = {}
        regDir = self.registryDirectory
        
        @inlineCallbacks
        def _addParametersInDirectory(topPath, subPath):
            yield self.client.registry.cd(topPath + subPath)
            directories,parameters = yield self.client.registry.dir()
            for parameter in parameters:
                value = yield self.client.registry.get(parameter)
                key = tuple(subPath + [parameter])
                self.parametersDict[key] = value
            if not len(directories):
                #bottom level directory is considered an experiment
                self.parametersDict[tuple(subPath + ['Semaphore','Block'])] = False
                self.parametersDict[tuple(subPath + ['Semaphore','Status'])] = 'Finished'
                self.parametersDict[tuple(subPath + ['Semaphore','Continue'])] = True
            for directory in directories:
                newpath = subPath + [directory]
                yield _addParametersInDirectory(topPath, newpath)
        #recursively add all parameters to the dictionary
        yield _addParametersInDirectory(regDir, []) 
        
    def _getParameterNames(self, path):
        names = []
        matching_keys = []
        for key in self.parametersDict.keys():
            if key[:len(path)] == path:
                matching_keys.append(key)
        if not len(matching_keys):
            raise Exception ("Wrong Directory or Empty Directory")
        else:
            for key in matching_keys:
                if len(key) == len(path) + 1: #exclude directories
                    names.append(key[-1])
        return names
    
    def _getAllNames(self, path):
        nest = self.parametersDict
        try:
            for key in path[:-1]:
                nest = nest[key]
            names = nest[path[-1]].keys()
        # in the root directory
        except IndexError:
            names = nest.keys()
        return names    

    def _getDirectoryNames(self, path):
        names = set()
        matching_keys = []
        for key in self.parametersDict.keys():
            if key[:len(path)] == path:
                matching_keys.append(key)
        if not len(matching_keys):
            raise Exception ("Wrong Directory or Empty Directory")
        else:
            for key in matching_keys:
                if len(key) > len(path) + 1: #exclude parameters
                    names.add(key[len(path)])
        return list(names)
   
    @inlineCallbacks
    def _saveParametersToRegistry(self):
        '''save the latest parameters into registry'''
        regDir = self.registryDirectory
        for key, value in self.parametersDict.iteritems():
            key = list(key)
            parameter_name = key.pop()
            fullDir = regDir + key
            if not fullDir[-1] == 'Semaphore':
                #don't save internal parameters which are found under 'semaphore' directory
                yield self.client.registry.cd(fullDir)
                yield self.client.registry.set(parameter_name, value)
   
    @inlineCallbacks            
    def _blockExperiment(self, status, block, cont):
        while(True):
            if (self.parametersDict[block] == False):
                shouldContinue = self.parametersDict[cont] 
                returnValue(shouldContinue)
            yield self.wait(0.1)
    
    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d

    @setting(0, "Set Parameter", path = '*s', value = ['*v', 'v', 'b', 's', '*(sv)', '*s', '?'], returns = '')
    def setParameter(self, c, path, value):
        """Set Parameter"""
        key = path.astuple
        if key not in self.parametersDict.keys():
            raise Exception ("Parameter Not Found")
        self.parametersDict[key] = value
        notified = self.getOtherListeners(c)
        self.onParameterChange((list(path), value), notified)

    @setting(1, "Get Parameter", path = '*s', returns = ['*v', 'v', 'b', 's', '*(sv)', '*s', '?'])
    def getParameter(self, c, path):
        """Get Parameter Value"""
        key = path.astuple
        if key not in self.parametersDict.keys():
            raise Exception ("Parameter Not Found")
        value = self.parametersDict[key]
        return value

    @setting(2, "Get Parameter Names", path = '*s', returns = '*s')
    def getParameterNames(self, c, path):
        """Get Parameter Names"""
        path = path.astuple
        parameterNames = self._getParameterNames(path)
        return parameterNames
    
    @setting(3, "Save Parameters To Registry", returns = '')
    def saveParametersToRegistry(self, c):
        """Get Experiment Parameter Names"""
        yield self._saveParametersToRegistry()
    
    @setting(4, "Get Directory Names", path = '*s', returns = '*s')
    def getDirectoryNames(self, c, path):
        """Get Directory Names"""
        path = path.astuple
        directoryNames = self._getDirectoryNames(path)
        return directoryNames    
        
    @setting(5, "Refresh Semaphore", returns = '')
    def refreshSemaphore(self, c):
        """Saves Parameters To Registry, then realods them """
        yield self._saveParametersToRegistry()
        yield self.loadDictionary()
    
    @setting(6, "Reload Semaphore", returns = '')
    def reloadSemaphore(self, c):
        """Discards current parameters and reloads them from registry"""
        yield self.loadDictionary()
    
    @setting(10, "Block Experiment", experiment = '*s', progress = 'v',  returns='b')
    def blockExperiment(self, c, experiment, progress = None):
        """Can be called from the experiment to see whether it could be continued"""
        status_key = tuple(list(experiment) + ['Semaphore', 'Status'])
        block_key = tuple(list(experiment) + ['Semaphore', 'Block'])
        continue_key = tuple(list(experiment) + ['Semaphore', 'Continue'])
        progress_key = tuple(list(experiment) + ['Semaphore', 'Progress'])
        if (progress != None):
            self.parametersDict[progress_key] = progress
            self.onParameterChange((list(progress_key), progress), self.listeners)
        if status_key not in self.parametersDict.keys():
            raise Exception ("Experiment Not Found or Has No Parameters")
        status = self.parametersDict[status_key]
        if (status == 'Pausing'):
            self.parametersDict[block_key] = True
            self.parametersDict[status_key] = 'Paused'
            self.onParameterChange((list(status_key), 'Paused'), self.listeners)
        result = yield self._blockExperiment(status_key, block_key, continue_key)
        returnValue(result)
    
    @setting(11, "Finish Experiment", path = '*s', progress = 'v', returns = '')
    def finishExperiment(self, c, path, progress=None):
        status_key = tuple(list(path) + ['Semaphore', 'Status'])
        progress_key = tuple(list(path) + ['Semaphore', 'Progress'])
        if status_key not in self.parametersDict.keys():
            raise Exception ("Experiment Not Found or Has No Parameters")
        if (progress == 100.0):
            self.parametersDict[status_key] = 'Finished'
            self.onParameterChange((list(status_key), 'Finished'), self.listeners)
            self.onParameterChange((list(progress_key), progress), self.listeners)
        else:
            self.parametersDict[status_key] = 'Stopped'
            self.onParameterChange((list(status_key), 'Stopped'), self.listeners)
    
    @setting(21, "Test Connection", returns = 's')
    def testConnection(self, c):
        return 'Connected!'
    
    @inlineCallbacks
    def stopServer(self):
        try:
            yield self._saveParametersToRegistry()
        except AttributeError:
            #if values don't exist yet, i.e stopServer was called due to an Identification Rrror
            pass
      
if __name__ == "__main__":
    from labrad import util
    util.runServer(Semaphore())