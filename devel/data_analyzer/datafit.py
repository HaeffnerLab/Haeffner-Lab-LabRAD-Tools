'''
Dylan Gorman

Container class for writing an arbitrary data fitting function

Populate a dictionary parameterDict with the initial parameters or 

set initial_guess = 'auto' to auto guess the parameter, otherwise set to some initial value

to_fit = True if you want to fit for this param, False to hold fixed

'''

from twisted.internet.defer import inlineCallbacks
import numpy as np
import lmfit

class DataFit():
    def __init__(self, raw):
        self.raw = raw # raw data

        self.parameterDict = {}
        
        r = np.array(self.raw)
        self.dataX = r[:,0]
        self.dataY = r[:,1]

        self.fitAccepted = False
        self.autoAccept = False

    def residual(self, params, x, data):
        model = self.model(params, x)
        return model - data
    
    def fit(self):

        params = lmfit.Parameters()
        
        '''
        Go through params and see which are set to auto guess, and then call
        self.guess() which should live in the inheriting type. then set up
        the lmfit parameters
        '''
        for p, (initial_guess, to_fit) in self.parameterDict.iteritems():

            if initial_guess == 'auto':
                initial_guess = self.guess(p)
                
            params.add(p, value = initial_guess, vary = to_fit)

        self.result = lmfit.minimize(self.residual, params, args = (self.dataX, self.dataY))
