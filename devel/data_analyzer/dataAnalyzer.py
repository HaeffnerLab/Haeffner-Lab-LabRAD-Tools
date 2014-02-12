'''
Dylan Gorman

Server for on-the-fly data analysis

The general flow should work like this:

1. Store a dataset into the databault with the parameter fit_type. fit_type can be either a
built in type such as RabiFlop, FrequencyScan, etc, or a custom type, e.g.
cct.scripts.custom_datasets.my_custom_dataset

2. load_data will import this module, so fit_type needs to refer to a module that
python can import. The module will contain a class named Fittable, which will contain the fitting routines
for this data type, some kind of automated initial value guessing, etc.

3. load_data returns a key (really an md5 hash of the datavault dir) by which the dataset can
be referred to outside the dataset.

4. populate parameters with add_parameter(). do add_parameter(key, 'param', 'auto') to autofit
Otherwise, do add_parameter(key, 'param', 'initial_guess'). the initial guess must be a string
here.

5. Once load_data() is called and the parameters are populated we can then call a fitting function

6. The fit function should optionally display the data together with the fit and allow
the user to accept or reject the fit. Reject -> either fit with custom params or do no fit at all.

'''

from labrad.server import setting, LabradServer, Signal
from labrad.units import WithUnit
from twisted.internet.defer import returnValue, inlineCallbacks
import importlib
import md5

class dataAnalyzer(LabradServer):

    """ Handles on-the-fly data analysis """

    name = 'Data Analyzer'

    #@inlineCallbacks
    def initServer(self):
        print "init"
        self.loaded_datasets = {}

    @setting(1, 'Load Data', path = '*s', dataset = ['i', 's'],  returns = 's')
    def load_data(self, c, path, dataset):
        ''' takes a dataset from datavault, and returns a key identifying the dataset '''
        dir = path
        context = yield self.client.context()
        yield self.client.data_vault.cd(dir, context = context)
        yield self.client.data_vault.open(dataset, context = context)

        # first see if there's a fit type specified in the datavault
        
        raw = yield self.client.data_vault.get(context=context)
        print raw
        fitTypePath = yield self.client.data_vault.get_parameter('fitTypePath', context=context)
        fitClass = yield self.client.data_vault.get_parameter('fitClass', context = context)
        print fitTypePath
        print fitClass
        module = importlib.import_module(fitTypePath)
        fitClass = getattr(module, fitClass)
        workspace = fitClass(raw)
  
        key = md5.new()
        key.update(str(dir)+str(dataset))

        self.loaded_datasets[key.digest()] = workspace
        
        returnValue(key.digest())

    @setting(2, 'Set Parameter', key = 's', param = 's', initial_guess = 'v', to_fit = 'b', is_auto = 'b', returns = '')
    def set_parameter(self, c, key, param, initial_guess, to_fit, is_auto = False):
        '''
        set a parameter with an initial guess.
        '''
        workspace = self.loaded_datasets[key]

        if is_auto:
            workspace.parameterDict[param] = ('auto', to_fit)
        else:
            workspace.parameterDict[param] = (initial_guess, to_fit)

    @setting(3, 'Fit', key='s', returns = '')
    def fit(self, c, key):
        ''' fit a loaded dataset '''

        workspace = self.loaded_datasets[key]
        workspace.fit()

    @setting(4, 'Get Parameter', key = 's', param = 's', returns = 'v')
    def get_parameter(self, c, key, param):

        ''' get a parameter that's already fitted.
        At some point add a check that the fit has
        actually occurred
        '''
        workspace = self.loaded_datasets[key]
        try:
            result = workspace.result
            return result.params[param].value
        except AttributeError:
            print "Data not fitted"
    
    @setting(5, 'Get ChiSqr', key = 's', returns = 'v')
    def get_chisqr(self, c, key):
        '''
        Get the chi-squared value for the fit returned by lmfit
        '''

        workspace = self.loaded_datasets[key]
        result = workspace.result
        
        return result.chisqr

    @setting(6, 'Get Error', key = 's', param = 's', returns = 'v')
    def get_error(self, c, key, param):
        '''
        Get the error on a fit parameter
        '''

        workspace = self.loaded_datasets[key]
        result = workspace.result
        
        return result.params[param].stderr

    @setting(7, 'Accept Fit', key = 's', returns = '')
    def accept_fit(self, c, key):
        '''
        Accept the results of a fit. Add to datavault
        and send a fit accepted signal
        '''
        workspace = self.loaded_datasets[key]
        workspace.fitAccepted = True

    @setting(8, 'Delete Workspace', key = 's', returns = '')
    def delete_workspace(self, c, key):
        '''
        Delete a workspace that is no longer needed
        '''
        
        del self.loaded_datasets[key]

if __name__=="__main__":
    from labrad import util
    util.runServer( dataAnalyzer() )
