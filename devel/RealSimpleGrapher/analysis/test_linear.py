# test for linear fits

from model_test import ModelTest
from fit_linear import Linear

test = ModelTest(Linear, 'Linear')
true_params = [0.3, 4]
test.generate_data(10, 20, 40, 1, true_params)
test.fit()
test.print_results()
test.plot()
