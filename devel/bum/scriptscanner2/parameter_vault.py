"""
### BEGIN NODE INFO
[info]
name = ParameterVault
version = 2.0
description = 
instancename = ParameterVault

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

class ParameterVault(LabradServer):
    
    name = "ParameterVault"
    
    """
    Data Server for storing ongoing experimental parameters
    """
    registryDirectory = ['','Servers', 'Parameter Vault']
    onParameterChange = Signal(612512, 'signal: parameter change', '(ss)')

#    @inlineCallbacks
#    def initServer(self):
#        """Load all of the paramters from the registry."""
#        self.listeners = set()
#        self.parameters = {}  
#        yield self.load_parameters()
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        """Expires the context object on disconnect."""
        self.listeners.remove(c.ID)   
        
    def getOtherListeners(self,c):
        """Returns the set of all listeners excluding the provided context c."""
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified
    
    @inlineCallbacks
    def load_parameters(self):
        """Recursively add all parameters to the dictionary."""
        yield self._addParametersInDirectory(self.registryDirectory, [])

    @inlineCallbacks
    def _addParametersInDirectory(self, topPath, subPath):
        """
        Navigate to the registry directory folder structure and load
        all of the parameters in the self.parameters dictionary
        """
        yield self.client.registry.cd(topPath + subPath, True)
        directories,parameters = yield self.client.registry.dir()
        if subPath: #ignore parameters in the top level
            for parameter in parameters:
                value = yield self.client.registry.get(parameter)
                key = tuple(subPath + [parameter])
                self.parameters[key] = value
        for directory in directories:
            newpath = subPath + [directory]
            yield self._addParametersInDirectory(topPath, newpath)

    def _get_parameter_names(self, collection):
        """Get names of all parameters in the given collection."""
        names = []
        for key in self.parameters.keys():
            if key[0] == collection:
                names.append(key[1])
        return names

    def _get_collections(self):
        """Get a list of all available collections."""
        names = set()
        for key in self.parameters.keys():
            names.add(key[0])
        return list(names)
   
    @inlineCallbacks
    def save_parameters(self):
        """save the latest parameters into registry."""
        regDir = self.registryDirectory
        for key, value in self.parameters.iteritems():
            key = list(key)
            parameter_name = key.pop()
            fullDir = regDir + key
            yield self.client.registry.cd(fullDir)
            yield self.client.registry.set(parameter_name, value)

    @inlineCallbacks
    def save_single_parameter(self, collection, parameter_name, value):
        regDir = []
        regDir.extend(self.registryDirectory)
        regDir.extend([collection])
        yield self.client.registry.cd(regDir, True)
        yield self.client.registry.set(parameter_name, value)
        
        
    def _save_full(self, key, value):
        """
        Checks the type parameter if the value falls within range
        If passes, returns the updated parameter
        """
        t,item = self.parameters[key]
        
        if t == 'parameter':
            assert item[0] <= value <= item[1], "Parameter {} Out of Bound".format(key[1])
            item[2] = value
            return (t, item)
        if t == 'string':
            # making sure that value is a string
            
            return (t, str(value))
            #return (t, item)
        if t == 'line_selection':
            # first check if the value is in the allowed dict
            if value in dict(item[1]).keys():
                return (t, (value, item[1]))
            else:
                raise NameError('Not allowed parameter did not update')
             
        if t == 'selection_simple':
            # first check if the value is in the allowed dict
            if value in item[1]:
                return (t, (value, item[1]))
            else:
                raise NameError('Not allowed parameter did not update')
             
        else:
            # Should we really do this and circumvent the exception here?? Philipp
            # In script scanner a boolean is set via the full_info. Does not wotk from a shell (The content is missing?)
            return (t, value)
            #raise Exception("Can't save, not one of checkable types") #TODO FIXME ??????????

    def all_parameters(self):
        """
        Return a dictionary with the settings of all current parameters
        with the key formatted as collection.parameter_name
        """
        d = {}
        for key in self.parameters.keys():
            collection, parameter_name = key
            k = '{}.{}'.format(collection, parameter_name)
            d[k] = self.check_parameter(key, self.parameters[key])
        return d

    def check_parameter(self, name, value):
        """
        Perform bound checking on the parameter
        """
        t,item = value
        #print name, t, t  == 'bool'
        if t == 'parameter' or t == 'duration_bandwidth':
            assert item[0] <= item[2] <= item[1], "Parameter {} Out of Bound".format(name)
            return item[2]
        elif t == 'string' or t == 'bool' or t == 'sideband_selection' or t == 'spectrum_sensitivity':
            return item
        elif t == 'scan':
            minim,maxim = item[0]
            start,stop,steps = item[1]
            assert minim <= start <= maxim, "Parameter {} Out of Bound".format(name)
            assert minim <= stop <= maxim, "Parameter {} Out of Bound".format(name)
            return (start, stop, steps)
        elif t == 'selection_simple':
            assert item[0] in item[1], "Inorrect selection made in {}".format(name)
            return item[0]
        elif t == 'line_selection':
            assert item[0] in dict(item[1]).keys(), "Inorrect selection made in {}".format(name)
            return item[0]
        else:#parameter type not known
            return value
        
    @setting(50, "Set Parameter", collection = 's', parameter_name = 's', value = '?', full_info = 'b', returns = '')
    def setParameter(self, c, collection, parameter_name, value, full_info = False):
        """Set a parameter value"""
        key = (collection, parameter_name)
        if key not in self.parameters.keys():
            raise Exception ("Parameter Not Found")
        if full_info:
            self.parameters[key] = value
        else:
            
            self.parameters[key] = self._save_full(key, value)
            
            
        notified = self.getOtherListeners(c)
        self.onParameterChange((key[0], key[1]), notified)

    @setting(51, "Get Parameter", collection = 's', parameter_name = 's', checked = 'b', returns = ['?'])
    def getParameter(self, c, collection, parameter_name, checked = True):
        """Get Parameter Value"""
        key = (collection, parameter_name)
               
        if key not in self.parameters.keys():
            raise Exception ("Parameter Not Found")
        result = self.parameters[key]
        if checked:
            result = self.check_parameter(key, result)
            
        t,item = self.parameters[key]
        return result

    @setting(52, 'New Parameter', collection = 's', parameter_name = 's', value = '?', returns = '')
    def new_parameter(self, c, collection, parameter_name, value):
        '''
        Create a new parameter, and save it in the registry
        value is a tuple of the form (t, val) where
        t is type of parameter, and value is a setting for
        that parameter
        '''
        key = (collection, parameter_name)
        if key in self.parameters.keys():
            raise Exception('Parameter already exists')
        else:
            self.parameters[key] = value
            yield self.save_single_parameter(collection, parameter_name, value)
            notified = self.getOtherListeners(c)
            #self.onParameterChange((key[0], key[1]), notified)
        
    @setting(53, "Get Parameter Names", collection = 's', returns = '*s')
    def getParameterNames(self, c, collection):
        """Get Parameter Names"""
        parameter_names = self._get_parameter_names(collection)
        return parameter_names
    
    @setting(54, "Save Parameters To Registry", returns = '')
    def saveParametersToRegistry(self, c):
        """Get Experiment Parameter Names"""
        yield self.save_parameters()
    
    @setting(55, "Get Collections", returns = '*s')
    def get_collection_names(self, c):
        collections = self._get_collections()
        return collections    
        
    @setting(56, "Refresh Parameters", returns = '')
    def refresh_parameters(self, c):
        """Saves Parameters To Registry, then realods them"""
        yield self.save_parameters()
        yield self.load_parameters()
    
    @setting(57, "Reload Parameters", returns = '')
    def reload_parameters(self, c):
        """Discards current parameters and reloads them from registry"""
        yield self.load_parameters()

    @setting(58, 'Verify Parameter Defined', collection = 's', parameter_name = 's', returns = 'b')
    def verify_parameter_defined(self, c, collection, parameter_name):
        key = (collection, parameter_name)
        if key in self.parameters.keys():
            return True
        else:
            return False

    @setting(59, 'Get All Parameters', returns = ['?'])
    def get_all_parameters(self, c):
        '''
        Return a list containing all parameters in the
        parametervault.
        '''
        return self.all_parameters().items()

    @inlineCallbacks
    def stopServer(self):
        try:
            yield self.save_parameters()
        except AttributeError:
            #if values don't exist yet, i.e stopServer was called due to an Identification Error
            pass
      
if __name__ == "__main__":
    from labrad import util
    util.runServer(ParameterVault())
