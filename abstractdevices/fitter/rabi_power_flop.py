from datafit import DataFit
import numpy as np

class Rabi_power_flop(DataFit):
    
    name = 'Rabi_power_flop'
    
    def __init__(self):
        super(Rabi_power_flop, self).__init__()
        self.all_parameters = ['target_power']
        self.guess_dict = {'target_power':self.guess_target_power}

    def guess(self, param):
        return self.guess_dict[param]()

    def guess_target_power(self):
        initial_target_power_guess = self.dataX[np.argmax(self.dataY)]
        return initial_target_power_guess

    def model(self, params, x):
        target_power = params['target_power'].value
        conversion = (2*10**(target_power/10))/np.pi
        power_data = 10**(x/10)
        rabi_freq = power_data/conversion
        model = (np.sin(rabi_freq))**2
        return model