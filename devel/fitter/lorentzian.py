from datafit import DataFit

class Lorentzian(DataFit):
    
    name = 'Lorentzian'
    
    def __init__(self):
        super(Lorentzian, self).__init__()
        self.all_parameters = ['Background', 'FWHM', 'Center', 'Height']
        self.guess_dict = {'FWHM':self.guess_fwhm, 'Center':self.guess_center,
                           'Height':self.guess_height, 'Background':self.guess_bgrnd}

    def guess(self, param):
        return self.guess_dict[param]()

    def guess_fwhm(self):
        xmax = self.dataX.max()
        xmin = self.dataX.min()
        return (xmax - xmin)/6.0

    def guess_center(self):
        j = list(self.dataY).index( self.dataY.max() )
        return self.dataX[j]
    
    def guess_height(self):
        return self.dataY.max()
    
    def guess_bgrnd(self):
        return 0

    def model(self, params, x):
        bgrnd = params['Background'].value
        fwhm = params['FWHM'].value
        center = params['Center'].value
        height = params['Height'].value
        gamma = fwhm/2.
        model = bgrnd + height*(gamma)**2/( (x - center)**2 + (gamma)**2)
        return model