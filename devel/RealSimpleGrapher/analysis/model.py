# Fitting wrapper class

class ParameterInfo():
    def __init__(self, parameter, index, guess_func, vary=True):
        self.parameter = parameter
        self.vary = vary
        self.guess_func = guess_func
        self.index = index

class Model():

    def __init__(self):
        pass

    def model(self):
        pass

    def guess_param(self, param, x, y):
        return self.parameters[param].guess_func(x, y)

    def reduced_model(self, x, p):
        '''
        reduced_model() allows model() to be optimized
        if certain parameters are to be held fixed.

        Suppose model() needs N parameters, but we want to hold
        k of them fixed. Then reduced_model() needs to accept
        N - k parameters.

        Procedure:
        full_params is an empty N-element list passed to model()
        First, fill in the parameters which are not varied
        into full_params.
        Then, whichever places are unfilled in full_params,
        fill them with the elements of p, an N - k parameter list.
        Evaluate model on full_params.
        '''

        n = len(self.parameters.keys())
        full_params = [None for k in range(n)]
        
        for key in self.parameters.keys():
            if not self.parameters[key].vary:
                index = self.parameters[key].index
                value = self.parameters[key].manual_value
                full_params[index] = value

        varied_positions = self.varied_positions()
        for index, k in zip(varied_positions, p):
            full_params[index] = k
        return self.model(x, full_params)

    def varied_positions(self):
        '''
        Indices of the parameters to vary in the fit
        '''
        varied = []
        for param in self.parameters.keys():
            if self.parameters[param].vary:
                varied.append(self.parameters[param].index)
        varied = sorted(varied)
        return varied

    def fixed_positions(self):
        '''
        Indicies of the parameters to hold fixed in the fit
        '''
        fixed = []
        for param in self.parameters.keys():
            if not self.parameters[param].vary:
                fixed.append(self.parameters[param].index)
        fixed = sorted(fixed)
        return fixed

    def param_from_index(self, index):
        '''
        Return a parameter from the index
        '''

        for param in self.parameters.keys():
            if self.parameters[param].index == index:
                return self.parameters[param]

        # parmeter not found
        raise Exception('Parameter not found')
