from lorentzian import Lorentzian
from rabi_power_flop import Rabi_power_flop

from analyzerWindow import AnalyzerWindow
from analyzerWindowSpectrum729 import analyzerWindow729, analyzerWindowPowerFlop

fitting_models = {
                  Lorentzian:analyzerWindow729,
                  Rabi_power_flop:analyzerWindowPowerFlop,
                  }

class FittingInterface(object):
    def __init__(self):
        self.all_fitting_models = {}
        self.active_model = None
        self.data = None
        self.manual_parameters = {}
        for model in fitting_models:
            self.all_fitting_models[model.name] = model
        self.accepted = None
        self.auto_accept = None
        
    def setAccepted(self, accepted):
        self.accepted = accepted
    
    def setAutoAccept(self, auto_accept):
        self.auto_accept = auto_accept
    
    def setModel(self, model):
        try:
            self.active_model = self.all_fitting_models[model]()
        except KeyError:
            raise Exception("Wrong model")
   
    def setData(self, data):
        self.data = data
    
    def addParameter(self, parameter, initial_guess, to_fit):
        self.manual_parameters[parameter]  = (to_fit, initial_guess)

    def start_fit(self):
        if not self.active_model:
            raise Exception("No fitting model selected")
        dataX, dataY = self.active_model.setData(self.data)
        self.active_model.setUserParameters(self.manual_parameters)
        fitX, fitY = self.active_model.fit()
        fitting_parameters = self.active_model.get_parameter_info()
        model_cls = self.active_model.__class__
        window_cls = fitting_models[model_cls]
        self.gui = window_cls(fitting_parameters, self.auto_accept, self)
        self.gui.plot(dataX, dataY, '*k')
        self.gui.plotfit(fitX, fitY)
        if self.auto_accept:
            self.accepted = True
        return self.gui
    
    def refit(self, gui_parameters):
        self.manual_parameters = gui_parameters 
        self.active_model.setUserParameters(self.manual_parameters)
        fitX, fitY = self.active_model.fit()
        fitting_parameters = self.active_model.get_parameter_info()
        self.gui.plotfit(fitX, fitY)
        self.gui.set_last_fit(fitting_parameters)
        
    def evaluate_params(self,params):
        evalX, evalY = self.active_model.evaluate_parameters(params)
        return evalX, evalY
    
    def get_parameter(self, parameter):
        return self.active_model.get_parameter_value(parameter)       