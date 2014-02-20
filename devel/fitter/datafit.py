import numpy as np
import lmfit

class DataFit(object):
    def __init__(self):
        self.params = None
        self.data = None
        self.manual_initial_values = {}
        self.all_parameters = []
        self.fitAccepted = False
        self.autoAccept = False
        
    def get_fitting_parameters(self):
        if self.params is None:
            self.params = lmfit.Parameters()
            for param in self.all_parameters:
                self.params.add(param)
        for parameter_name in self.all_parameters:
            if parameter_name in self.manual_initial_values:
                initial_guess, to_fit = self.manual_initial_values[parameter_name]
            else:
                to_fit = True
                initial_guess = self.guess(parameter_name)
            self.params[parameter_name].vary = to_fit
            self.params[parameter_name].value = initial_guess
        
    def setData(self, data):
        r = np.array(data)
        self.dataX = r[:,0]
        self.dataY = r[:,1]
        return self.dataX, self.dataY
            
    def setUserParameters(self, params):
        self.manual_initial_values = params

    def residual(self, params, x, data):
        model = self.model(params, x)
        return model - data
    
    def fit(self):
        '''
        Go through params and see which are set to auto guess, and then call
        self.guess() which should live in the inheriting type. then set up
        the lmfit parameters
        '''
        self.get_fitting_parameters()
        self.result = lmfit.minimize(self.residual, self.params, args = (self.dataX, self.dataY))
        self.fitAccepted = True
        points = len(self.dataX)
        fine_grid = np.linspace(self.dataX.min(), self.dataX.max(), 100 * points)
        y_values = self.model(self.params, fine_grid)
        return fine_grid, y_values
    
    def get_parameter_info(self):
        info = {}
        for p in self.all_parameters:
            #(name, to_fit, auto_fit, user_guess, value)
            auto_fit = p not in self.manual_initial_values
            man_value = self.manual_initial_values.get(p)
            info[p] = (self.params[p].vary, auto_fit, man_value, self.params[p].value)
        return info
    
    def get_parameter_value(self, parameter):
        try:
            value = self.params[parameter].value
        except KeyError:
            raise Exception("No such parameter")
        else:
            return value 
    
    def evaluate_parameters(self, params):
        test_parameters = lmfit.Parameters()
        for name, value in params.iteritems():
            test_parameters.add(name, value)
        points = len(self.dataX)
        fine_grid = np.linspace(self.dataX.min(), self.dataX.max(), 100 * points)
        y_values = self.model(test_parameters, fine_grid)
        return fine_grid, y_values