# Generic fitter class

from scipy import optimize
from fit_lorentzian import Lorentzian

class FitWrapper():

    models = ['Lorentzian', 'Gaussian', 'Rabi']

    def __init__(self, dataset, index):
        self.dataset = dataset
        self.index = index

    def setModel(self, model):
        self.model = Lorentzian()

    def getParameters(self):
        return self.model.parameters.keys()

    def getVary(self, p):
        return self.model.parameters[p].vary

    def getManualValue(self, p):
        try:
            return self.model.parameters[p].manual_value
        except: # value doesn't exist. Use automatic guess
            x = self.dataset.data[:,0]
            y = self.dataset.data[:,self.index+1]
            guess = self.model.guess_param(p, x, y)
            self.model.parameters[p].manual_value = guess
            return guess
            
    def getFittedValue(self, p):
        try:
            return self.model.parameters[p].fitted_value
        except: # no fitted value exists yet
            return None

    def setManualValue(self, p, value):
        self.model.parameters[p].manual_value = value
        
    def setVary(self, p, value):
        assert value is True or False
        self.model.parameters[p].vary = value

    def doFit(self):
        
        x = self.dataset.data[:,0]
        y = self.dataset.data[:, self.index + 1]
        
        def residual(p):
            return y -  self.model.reduced_model(p, x)

        varied_positions = self.model.varied_positions()
        fixed_positions = self.model.fixed_positions()
        x0 = [self.model.param_from_index(k).manual_value for k in varied_positions]
        result = optimize.leastsq(residual, x0)
        result = result[0]

        # after the fit, assign the fitted values to the parameters
        # For the fixed parameters, set the fit_value = manual_value
        # so that we don't have to deal with it in the GUI display
        for pos, fit_val in zip(varied_positions, result):
            param = self.model.param_from_index(pos)
            param.fit_value = fit_val

        for pos in fixed_positions:
            param = self.model.param_from_index(pos)
            param.fit_value = param.manual_value
