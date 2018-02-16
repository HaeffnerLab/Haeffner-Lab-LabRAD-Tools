"""
readouts.py

Methods for analyzing PMT or camera data

"""

import numpy as np
import lmfit
from equilibrium_positions import position_dict
from ion_state_detector import ion_state_detector
import peakutils

def pmt_simple(readouts, threshold , readout_mode = 'pmt'):
    """
    Method for analyzing pmt data with a single threshold value.
    Takes the readouts from the pulser as well as the parameters
    dictionary. Returns excitation probability.
    """

    if len(readouts):
        
        threshold_list=[int(float(x)) for x in threshold.split(',')]
        
        if len(threshold_list) == 1:
            # regular pmt stuff
            perc_excited = [np.count_nonzero(readouts <= threshold_list[0]) / float(len(readouts))]
        
        else:
            
            threshold_list = sorted(threshold_list)
            #print np.array(readouts)
            num_ions = len(threshold_list)
            #print "working with {}  ions".format(num_ions)
            #print threshold_list
            binned = np.histogram(readouts, bins=[0]+threshold_list)[0]
            #IPython.embed()
            #print binned
            N = float(len(readouts))
#             print " 555"
#             print "number of meas is ", N
#             print readouts
            perc_excited = binned/N
            #mean = numpy.dot(binned, range(num_ions+1)) # avg number of ions dark

    else:
        # got no readouts
        perc_excited = [-1.0]
    
    # calculating the probability of zero dark ions
    prob_0= 1.0 - np.sum(np.array(perc_excited))
    
    
    if readout_mode == 'pmt_states': 
        perc_excited=np.append(perc_excited,[prob_0])
        
    if readout_mode == 'pmt_parity': 
        ## add the calculation for the parity
        num_ions=len(perc_excited)
        # adding the zero prob.
        perc_excited=np.append(perc_excited,[prob_0])
        
        # parity id defined to be Poevev-Podd (even number of S ions SSS-> negative parity )
        ## inconsistent with the parity 
        parity= [(-1.0)**(num_ions-i)*perc_excited[i] for i in range(len(perc_excited))]
        parity=np.sum(np.array(parity))
        # calculate the parity
        perc_excited=np.append(perc_excited,[parity])
 
       
   
    return perc_excited 
    


def get_states_PMT(readouts):
    pass
def calc_parity_PMT():
    pass

def camera_ion_probabilities(images, repetitions, p, readout_mode = 'camera'):
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
    #np.save('temp_camera_ion_state', ion_state)
    #np.save('temp_camera_readout', readouts)
    
    
    if readout_mode == 'camera_states':
        ion_state=get_states_camera(readouts,int(p.ion_number))
        
    if readout_mode == 'camera_parity':
        ion_state=get_states_camera(readouts,int(p.ion_number))
        parity= Calc_parity(ion_state)
        ion_state=np.append(ion_state,[parity])
    
#     print "555"
#     print "readout_mode", readout_mode
#     print "ion_stste", ion_state
#         
    return ion_state, readouts, confidences

def bool2int(x):
    y = 0
    for i,j in enumerate(x):
        y += j<<i
    return y

def get_states_camera(readouts,num_of_ions):
    # number of experiments
    N = float(len(readouts))
    counts= np.zeros(2**num_of_ions)
    for readout in readouts:
        index= bool2int(1-readout)
        counts[index]  +=1
    counts_in_states=1.0*counts/N
    return counts_in_states
        
def Calc_parity(Probs):
    Parity=0.0
    for i, prob in enumerate(Probs):
        s=np.binary_repr(i)
        Parity += 1.0*prob*(-1)**s.count('1')
    return Parity


def get_states(readouts):
    # function that calculates from the camera readout the two ion states 
    SS = np.array([1, 1])
    SD = np.array([1, 0])
    DS = np.array([0, 1])
    DD = np.array([0, 0])
        
    numSS = 0
    numSD = 0
    numDS = 0
    numDD = 0
    for readout in readouts:
        if np.array_equal(readout, SS): numSS += 1
        elif np.array_equal(readout, SD): numSD += 1
        elif np.array_equal(readout, DS): numDS += 1
        elif np.array_equal(readout, DD): numDD += 1
    N = float(len(readouts))
    return [numSS/N, numSD/N, numDS/N, numDD/N ]


