# Generic class for testing
# models and fitting

import numpy as np
import matplotlib.pyplot as plt
from fitting import FitWrapper

class ModelTest():
    
    def __init__(self, cls, name):
        '''
        cls: model class
        name: string to pass to FitWrapper
        '''
        self.cls = cls()
        self.name = name

    def generate_data(self, xmin, xmax, steps, noise, true_params):
        '''
        Generate noisy data around the model
        '''
        
        class dataset():
            def __init__(self, x, y):
                N = len(x)
                self.data = np.zeros((N,2))
                self.data[:,0] = x
                self.data[:,1] = y

        x = np.linspace(xmin, xmax, steps)
        self.true_params = true_params
        y = self.cls.model(x, true_params) + noise*np.random.normal(size=len(x))
        ds = dataset(x, y)
        self.fw = FitWrapper(ds, 0)
        self.fw.setModel(self.name)

        for p in self.fw.getParameters():
            self.fw.getManualValue(p) # force guess of initial parameters

        self.x = x
        self.y = y

    def fit(self):
        self.fw.doFit()
        
    def plot(self, fit = True):
        plt.plot(self.x, self.y, 'ro')
        if fit:
            output = self.fw.evaluateFittedParameters() 
            plt.plot(output[:,0], output[:,1])
        plt.show()
        
    def print_results(self):
        
        print '***** FIT RESULTS *****'
        print '{}\t{}\t{}'.format('PARAM','TRUE','FITTED')
        for i, p in enumerate(self.fw.getParameters()):
            print '{}\t{}\t{}'.format(p, self.true_params[i], self.fw.getFittedValue(p))
