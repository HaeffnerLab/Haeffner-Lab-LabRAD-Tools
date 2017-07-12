"""
readouts.py

Methods for analyzing PMT or camera data

"""

import numpy as np
import lmfit
from equilibrium_positions import position_dict
from ion_state_detector import ion_state_detector
import peakutils

def pmt_simple(readouts, threshold):
    """
    Method for analyzing pmt data with a single threshold value.
    Takes the readouts from the pulser as well as the parameters
    dictionary. Returns excitation probability.
    """

    if len(readouts):
        perc_excited = np.count_nonzero(readouts <= threshold) / float(len(readouts))
    else:
        # got no readouts
        perc_excited = -1.0
    return [perc_excited]

def camera_ion_probabilities(images, repetitions, p):
    """
    Method for analyzing camera images. For an
    N-ion chain, returns an N element list
    indicating the probability that each
    ion is excited.
    """

    fitter = ion_state_detector(int(p.ion_number))

    image_region = [
                             int(p.horizontal_bin),
                             int(p.vertical_bin),
                             int(p.horizontal_min),
                             int(p.horizontal_max),
                             int(p.vertical_min),
                             int(p.vertical_max),
                             ]
    fit_parameters = lmfit_Parameters()
    fit_parameters.add('ion_number', value = int(p.ion_number))
    fit_parameters.add('background_level', value = p.fit_background_level)
    fit_parameters.add('amplitude', value = p.fit_amplitude)
    fit_parameters.add('rotation_angle', p.fit_rotation_angle)
    fit_parameters.add('center_x', value = p.fit_center_horizontal)
    fit_parameters.add('center_y', value = p.fit_center_vertical)
    fit_parameters.add('spacing', value = p.fit_spacing)
    fit_parameters.add('sigma', value = p.fit_sigma)
    x_axis = numpy.arange(image_region[2], image_region[3] + 1, image_region[0])
    y_axis = numpy.arange(image_region[4], image_region[5] + 1, image_region[1])
    xx,yy = numpy.meshgrid(x_axis, y_axis)
    fitter.set_fitted_parameters(fit_parameters, xx, yy)
   
    x_pixels = int( (image_region[3] - image_region[2] + 1.) / (image_region[0]) )
    y_pixels = int(image_region[5] - image_region[4] + 1.) / (image_region[1])
    images = numpy.reshape(images, (repetitions, y_pixels, x_pixels))
    readouts, confidences = fitter.state_detection(images)

    ion_state = 1 - readouts.mean(axis = 0)
    
    return ion_state, readouts, confidences
