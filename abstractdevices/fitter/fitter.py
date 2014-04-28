#install qt4 reactor for the GUI
from PyQt4 import QtGui
a = QtGui.QApplication( [])
import qt4reactor
qt4reactor.install()
from twisted.internet import reactor
from labrad.server import setting, LabradServer
from labrad.types import Error
from fitting_interface import FittingInterface
from twisted.internet.defer import returnValue, Deferred

class fitter(LabradServer):

    """ Handles on-the-fly data analysis """

    name = 'Fitter'

    def initServer(self):
        pass

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
        fitting_interface.addParameter(param, to_fit = to_fit, auto_guess = False, initial_guess = initial_guess)

    @setting(3, 'Fit', model='s', auto_accept = 'b', returns = '')
    def fit(self, c, model = None, auto_accept = False):
        ''' fit a loaded dataset '''
        fitting_interface = c['fitting_interface']
        if model is not None:
            fitting_interface.setModel(model)
        fitting_interface.setAutoAccept(auto_accept)
        window = fitting_interface.start_fit()

    @setting(4, 'Get Parameter', param = 's', returns = 'v')
    def get_parameter(self, c, param):
        ''' get a parameter that's already fitted'''
        fitting_interface = c['fitting_interface']
        return fitting_interface.get_parameter(param)
    
    @setting(5, 'Wait For Acceptance', timeout = 'v', returns = 'b')
    def wait_for_acceptance(self, c, timeout = None):
        if timeout is None:
            timeout = 60.0#seconds
        check_period = 1#second
        check_range = int(timeout / check_period)
        fitting_interface = c['fitting_interface']
        for i in range(check_range):
            if fitting_interface.accepted is not None:
                returnValue(fitting_interface.accepted)
            else:
                yield self.wait(check_period)
        returnValue(False)
    
    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d
    
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
    util.runServer( fitter() )
