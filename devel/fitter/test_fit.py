import labrad
cxn = labrad.connect()
fitter = cxn.fitter
directory = (['', 'Experiments', 'Spectrum729', '2014Feb10', '1347_48'],1)
fitter.load_data(directory)
# fitter.fit('Lorentzian')
fitter.fit('Lorentzian', True)


accepted = fitter.wait_for_acceptance()

if accepted:
    print fitter.get_parameter('Center')
    print fitter.get_parameter('FWHM')
else:
    print 'fit rejected!'