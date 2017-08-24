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
        
        threshold_list=[int(x) for x in threshold.split(',')]
        
        if len(threshold_list) == 1:
            # regular pmt stuff
            perc_excited = [np.count_nonzero(readouts <= threshold_list[0]) / float(len(readouts))]
        
        else:
            
            threshold_list = sorted(threshold_list)
            #print np.array(readouts)
            num_ions = len(threshold_list)
            print "working with {}  ions".format(num_ions)
            #print threshold_list
            binned = np.histogram(readouts, bins=[0]+threshold_list)[0]
            #IPython.embed()
            #print binned
            N = float(len(readouts))
            perc_excited = binned/N
            #mean = numpy.dot(binned, range(num_ions+1)) # avg number of ions dark

    else:
        # got no readouts
        perc_excited = [-1.0]
    
    np.save('temp_PMT', perc_excited)
    print "saved ion data"
    
    return perc_excited

def camera_ion_probabilities(images, repetitions, p):
    """
    Method for analyzing camera images. For an
    N-ion chain, returns an N element list
    indicating the probability that each
    ion is excited.
    """
    from lmfit import Parameters as lmfit_Parameters
    
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
    x_axis = np.arange(image_region[2], image_region[3] + 1, image_region[0])
    y_axis = np.arange(image_region[4], image_region[5] + 1, image_region[1])
    xx,yy = np.meshgrid(x_axis, y_axis)
    fitter.set_fitted_parameters(fit_parameters, xx, yy)
   
    x_pixels = int( (image_region[3] - image_region[2] + 1.) / (image_region[0]) )
    y_pixels = int( (image_region[5] - image_region[4] + 1.) / (image_region[1]) )
    #print "inside the camera readout"
    #print "x_pixels {}".format(x_pixels)
    #print "y_pixels {}".format(y_pixels)
    #print images
    #np.save('37ions_global', images)
    #print "repetitions{}".format(repetitions)
    
    images = np.reshape(images, (repetitions, y_pixels, x_pixels))
    readouts, confidences = fitter.state_detection(images)

    ion_state = 1 - readouts.mean(axis = 0)
    np.save('temp_camera', ion_state)
    print "saved ion data"
    return ion_state, readouts, confidences
