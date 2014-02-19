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
#install qt4 reactor for the GUI
from PyQt4 import QtGui
a = QtGui.QApplication( [])
import qt4reactor
qt4reactor.install()
from labrad.server import setting, LabradServer
from labrad.types import Error
from fitting_interface import FittingInterface

class dataAnalyzer(LabradServer):

    """ Handles on-the-fly data analysis """

    name = 'Data Analyzer'

    def initServer(self):
        self.window_list = []

    @setting(1, 'Load Data', path = '*s', dataset = ['i', 's'])
    def load_data(self, c, path, dataset):
        ''' takes a dataset from datavault, and returns a key identifying the dataset '''
        fitting_interface = c['fitting_interface']
        yield self.client.data_vault.cd(path)
        yield self.client.data_vault.open(dataset)
        data = yield self.client.data_vault.get()
        try:
            model_name = yield self.client.data_vault.get_parameter('fitting_model')
            fitting_interface.setModel(model_name)
        except Error as e:
            if e.code == 9:
                #no model preference
                pass
            else:
                raise
        fitting_interface.setData(data)
            

    @setting(2, 'Set Parameter', param = 's', initial_guess = 'v', to_fit = 'b', returns = '')
    def set_parameter(self, c, param, initial_guess, to_fit):
        '''
        set a parameter with an initial guess.
        '''
        fitting_interface = c['fitting_interface']
        fitting_interface.addParameter(param, initial_guess, to_fit)

    @setting(3, 'Fit', model='s', returns = '')
    def fit(self, c, model = None):
        ''' fit a loaded dataset '''
        fitting_interface = c['fitting_interface']
        if model is not None:
            fitting_interface.setModel(model)
        window = fitting_interface.start_fit()
        self.window_list.append(window)

    @setting(4, 'Get Parameter', param = 's', returns = 'v')
    def get_parameter(self, c, param):
        ''' get a parameter that's already fitted'''
        fitting_interface = c['fitting_interface']
        return fitting_interface.get_parameter(param)
    
#     @setting(5, 'Get ChiSqr', key = 's', returns = 'v')
#     def get_chisqr(self, c, key):
#         '''
#         Get the chi-squared value for the fit returned by lmfit
#         '''
#         workspace = self.loaded_datasets[key]
#         result = workspace.result
#         return result.chisqr
# 
#     @setting(6, 'Get Error', key = 's', param = 's', returns = 'v')
#     def get_error(self, c, key, param):
#         '''
#         Get the error on a fit parameter
#         '''
#         workspace = self.loaded_datasets[key]
#         result = workspace.result
#         return result.params[param].stderr
    
    def initContext(self, c):
        c['fitting_interface'] = FittingInterface()

if __name__=="__main__":
    from labrad import util
    util.runServer( dataAnalyzer() )
