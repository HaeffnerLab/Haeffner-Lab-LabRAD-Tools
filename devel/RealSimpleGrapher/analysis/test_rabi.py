# test for Rabi flop fits

from model_test import ModelTest
from fit_rabi import Rabi

import numpy as np


test = ModelTest(Rabi, 'Rabi')
true_params = [2*np.pi/(10), 10, 0.05, 0., 0, 0.6]
test.generate_data(0, 30, 300, 0.02, true_params)
test.fit()
test.print_results()
test.plot(fit=True)
