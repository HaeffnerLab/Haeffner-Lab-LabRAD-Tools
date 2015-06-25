import labrad
cxn = labrad.connect()
fitter = cxn.fitter
#directory = (['', 'Experiments', 'Spectrum729', '2014Feb10', '1347_48'],1)

directory = (['','Experiments','Rabi_power_flopping_2ions','2014Mar16','1216_19'],1)

fitter.load_data(directory)
# fitter.fit('Lorentzian')
fitter.fit('Rabi_power_flop', False)


accepted = fitter.wait_for_acceptance()

if accepted:
    print fitter.get_parameter('target_power')
else:
    print 'fit rejected!'