import numpy as np
import lmfit
from equilibrium_positions import position_dict
import peakutils

from multiprocessing import Process

class ion_state_detector(object):
    
    def __init__(self, ion_number):
        self.ion_number = ion_number
        self.all_state_combinations = self.all_combinations_0_1(ion_number)
        self.spacing_dict = position_dict[ion_number] #provides relative spacings of all the ions
        self.fitted_gaussians, self.background = None, None

    def integrate_image_vertically(self, data, threshold):
        # sum image vertically        
        v_sum = data.sum(0)

        v_sum = v_sum - np.min(v_sum)

        if np.max(v_sum) > 200:
            #v_sum = v_sum/np.max(v_sum)

            indices = peakutils.indexes(v_sum, thres=threshold, min_dist = 2)

            #print indices
            try:
                self.plot_integrated_image(v_sum)
            except:
                pass
        else:
            indices = []
        
        # return the number of ions
        return len(indices)

    def plot_integrated_image(self, v_sum):
        from matplotlib import pyplot
        pyplot.plot(v_sum)
        pyplot.plot(0.4 * np.ones(len(v_sum)))
        pyplot.tight_layout()
        pyplot.show()


    def set_fitted_parameters(self, params, xx, yy):
        self.fitted_gaussians = self.ion_gaussians(params, xx, yy)
        self.background = params['background_level'].value
    
    def gaussian_2D(self, xx, yy, x_center, y_center, sigma_x, sigma_y, amplitude):
        '''
        xx and yy are the provided meshgrid of x and y coordinates
        generates a 2D gaussian for centered at x_center and y_center
        '''
        result = amplitude * np.exp( - (xx - x_center)**2 / (2 * sigma_x**2)) *  np.exp( - (yy - y_center)**2 / (2 * sigma_y**2))
        return result
    
    def ion_gaussians(self, params, xx, yy):
        '''
        N is params['ion_number']
        
        returns a (N-long) array where i-th element corresponds to the gaussian centered at the i-th ion.
        '''
        ion_gaussians  = np.empty((self.ion_number, xx.shape[0], xx.shape[1]))
        amplitude = params['amplitude'].value #all ions are assumsed to have the same amplitude
        rotation_angle = params['rotation_angle'].value #angle of the ion axis with respect to the xx and yy coordinate system
        ion_center_x = params['center_x'].value #center of the ions
        ion_center_y = params['center_y'].value #center of the ions
        spacing = params['spacing'].value #spacing constant of the ions
        sigma = params['sigma'].value #width along the axis
        #first we rotate the data by the rotation_angle about the ion center
        xx_rotated = ion_center_x +  (xx - ion_center_x) * np.cos(rotation_angle) - (yy - ion_center_y) * np.sin(rotation_angle)
        yy_rotated = ion_center_y +  (xx - ion_center_x) * np.sin(rotation_angle) + (yy - ion_center_y) * np.cos(rotation_angle)
        for i in range(self.ion_number):
            ion_gaussians[i] = self.gaussian_2D(xx_rotated, yy_rotated, ion_center_x + spacing * self.spacing_dict[i], ion_center_y, sigma, sigma, amplitude)
        return ion_gaussians
  
    def ion_model(self, params, xx, yy):
        '''
        calcultes the sum of the background and all the gaussians centered at every ion
        '''
        summed_gaussians = params['background_level'].value + self.ion_gaussians(params, xx, yy).sum(axis = 0)
        return summed_gaussians

    def cartesian_product(self, arrays):
        '''
        http://stackoverflow.com/questions/1208118/using-numpy-to-build-an-array-of-all-combinations-of-two-arrays
        '''
        broadcastable = np.ix_(*arrays)
        broadcasted = np.broadcast_arrays(*broadcastable)
        rows, cols = reduce(np.multiply, broadcasted[0].shape), len(broadcasted)
        out = np.empty(rows * cols, dtype=broadcasted[0].dtype)
        start, end = 0, rows
        for a in broadcasted:
            out[start:end] = a.reshape(-1)
            start, end = end, end + rows
        return out.reshape(cols, rows).T
    
    def all_combinations_0_1(self, n):
        '''
        create all comibations of  (0) and (1)
        
        i.e
        
        2 -> [[0,0],[0,1],[1,0],[1,1]]
        3 -> [[0,0,0],[0,0,1],...,[1,1,1]]
        '''
        return self.cartesian_product([[0,1] for i in range(n)])
    
    def fitting_error(self, params , xx, yy,  data):
        model = self.ion_model(params, xx, yy)
        scaled_difference = (model - data) / np.sqrt(data)
        return scaled_difference.ravel()
    
    def fitting_error_state(self, selection, image):
        '''
        '''
        sum_selected_gaussians = self.background + np.tensordot(selection, self.fitted_gaussians, axes = (1, 0))
        sum_selected_gaussians = sum_selected_gaussians[:, None, :, :]
        image_size = float(image.shape[1] * image.shape[2]) 
        chi_sq = (sum_selected_gaussians - image)**2 / image / image_size
        chi_sq = chi_sq.sum(axis = (2,3))
        best_states = selection[np.argmin(chi_sq, axis = 0)]
        sorted_chi = np.sort(chi_sq, axis = 0)
        lowest_chi,second_lowest_chi = sorted_chi[0:2]
        confidence = 1 - lowest_chi / second_lowest_chi
        return best_states, confidence

    def guess_parameters_and_fit(self, xx, yy, data):
        params = lmfit.Parameters() 
        background_guess = data[0].mean() #assumes that there are no ions at the edge of the image
        background_std = np.std(data[0])
        center_x_guess,center_y_guess,amplitude_guess, spacing_guess = self.guess_centers(data, background_guess, background_std, xx, yy)
        sigma_guess = 1#assume it's hard to resolve the ion, sigma ~ 1
        params.add('background_level', value = background_guess, min = 0.0)
        params.add('amplitude', value = amplitude_guess, min = 0.0)
        params.add('rotation_angle', value = 0.0001, min = -np.pi, max = np.pi, vary = False)
        params.add('center_x', value = center_x_guess, min = xx.min(), max = xx.max())
        params.add('center_y', value = center_y_guess, min = yy.min(), max = yy.max())
        params.add('spacing', value = spacing_guess, min = 2.0, max = 60)
        params.add('sigma', value = sigma_guess, min = 0.01, max = 10.0)
        #first fit without the angle
        lmfit.minimize(self.fitting_error, params, args = (xx, yy, data))
        #allow angle to vary and then fit again
        params['rotation_angle'].vary = True
        result = lmfit.minimize(self.fitting_error, params, args = (xx, yy, data))
        self.set_fitted_parameters(params, xx, yy)
        return result, params
    
    def guess_centers(self, data, background, background_std, xx, yy):
        '''
        guesses the center of the ion from the data
        
        starts with a threshold of 3 standard deviations above the background and gets 
        the average positions of all pixels higher than this value
        
        if none are found, lowers the threshold
        '''
        thresholds = np.arange(3,0,-1)
        for threshold in thresholds:
            #print threshold
            peak_discrimination = background + threshold * background_std
            where_peak = np.where(data > peak_discrimination)
            peaks_y, peaks_x = yy[where_peak], xx[where_peak]
            if peaks_x.size and peaks_y.size:
                center_y_guess= peaks_y.mean()
                center_x_guess = peaks_x.mean()
                amplitude_guess = data[where_peak].mean()
                if not self.ion_number == 1:
                    #see Michael Ramm writeup, spacing guess for this
                    where_peak = np.where(data > amplitude_guess)
                    peaks_y, peaks_x = yy[where_peak], xx[where_peak]
                    std = np.sqrt(peaks_x.std()**2 + peaks_y.std()**2)
                    sumsq = np.sum(np.array(self.spacing_dict)**2)
                    spacing_guess = std * np.sqrt(self.ion_number / sumsq)
                else:
                    spacing_guess = 0
                return center_x_guess, center_y_guess, amplitude_guess, spacing_guess
        raise Exception("Unable to guess ion center from the data")
    
    def get_total_counts(self, image):
        '''
        returns the total number of ion counts
        
        This is done by multiplying the given image by the fit.
        '''
        if self.fitted_gaussians is None:
            raise Exception("Fitted parameters not provided")
        if image.ndim == 2:
            #if only a single image is provided, shape it to be a 1-long sequence
            image = image.reshape((1, image.shape[0],image.shape[1]))
        
        gaussians = self.fitted_gaussians / self.fitted_gaussians.max()
        return np.sum(gaussians * image, axis = (1,2))
        
    def state_detection(self, image):
        '''
        given the image and the parameters of the reference images with all ions bright, determines
        which ions are currently darks
        '''
        if self.fitted_gaussians is None:
            raise Exception("Fitted parameters not provided")
        if image.ndim == 2:
            #if only a single image is provided, shape it to be a 1-long sequence
            image = image.reshape((1, image.shape[0],image.shape[1]))
        state, confidence = self.fitting_error_state(self.all_state_combinations, image)
        return state, confidence

    def report(self, params):
        lmfit.report_errors(params)
    
    def graph(self, x_axis, y_axis, image, params, result = None):
        #plot the sample data
        from matplotlib import pyplot
        pyplot.contourf(x_axis, y_axis, image, alpha = 0.5)
        #plot the fit
        #sample the fit with more precision
        x_axis_fit = np.linspace(x_axis.min(), x_axis.max(), x_axis.size * 5)
        y_axis_fit = np.linspace(y_axis.min(), y_axis.max(), y_axis.size * 5)
        xx, yy = np.meshgrid(x_axis_fit, y_axis_fit)
        fit = self.ion_model(params, xx, yy)
        pyplot.contour(x_axis_fit, y_axis_fit, fit, colors = 'k', alpha = 0.75)
        if result is not None:
            pyplot.annotate('chi sqr {}'.format(result.redchi), (0.5,0.8), xycoords = 'axes fraction')
        pyplot.tight_layout()
        pyplot.show()
