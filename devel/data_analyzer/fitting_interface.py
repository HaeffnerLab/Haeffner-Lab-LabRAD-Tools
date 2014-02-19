from lorentzian import Lorentzian

from analyzerWindow import AnalyzerWindow

fitting_models = [Lorentzian]

class FittingInterface(object):
    def __init__(self):
        self.all_fitting_models = {}
        self.active_model = None
        self.data = None
        self.manual_parameters = {}
        for model in fitting_models:
            self.all_fitting_models[model.name] = model
    
    def setModel(self, model):
        try:
            self.active_model = self.all_fitting_models[model]()
        except KeyError:
            raise Exception("Wrong model")
   
    def setData(self, data):
        self.data = data
    
    def addParameter(self, parameter, initial_guess, to_fit):
        self.params[parameter, initial_guess, to_fit]

    def start_fit(self):
        if not self.active_model:
            raise Exception("No fitting model selected")
        dataX, dataY = self.active_model.setData(self.data)
        self.active_model.setUserParameters(self.manual_parameters)
        fitX, fitY = self.active_model.fit()
        fitting_parameters = self.active_model.get_parameter_info()
        print fitting_parameters
        self.gui = AnalyzerWindow(fitting_parameters, self)
        self.gui.plot(dataX, dataY, '*k')
        self.gui.plot(fitX, fitY, 'r')
        return self.gui
    
    def evaluate_params(self,params):
        evalX, evalY = self.active_model.evaluate_parameters(params)
        return evalX, evalY
    
    def get_parameter(self, parameter):
        return self.active_model.get_parameter_value(parameter)       