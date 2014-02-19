import labrad
cxn = labrad.connect()
fitter = cxn.data_analyzer
directory = (['', 'Experiments', 'Spectrum729', '2014Feb10', '1347_48'],1)
fitter.load_data(directory)
fitter.fit('Lorentzian')
print fitter.get_parameter('FWHM')
print fitter.get_parameter('Center')
print 'DONe'