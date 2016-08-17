# test for Gaussian fits

from model_test import ModelTest
from fit_gaussian import Gaussian

test = ModelTest(Gaussian, 'Gaussian')
true_params = [130., 4., 5., 0.1]
test.generate_data(100, 200, 200, 0.02, true_params)
test.fit()
test.print_results()
test.plot()
