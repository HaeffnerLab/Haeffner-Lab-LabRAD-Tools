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

        

        
        
