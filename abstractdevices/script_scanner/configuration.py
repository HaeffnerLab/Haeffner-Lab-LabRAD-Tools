class config(object):

    #list in the format (import_path, class_name)
    scripts = [
               ('lattice.scripts.experiments.FFT.fft_spectrum', 'fft_spectrum'), 
               ('lattice.scripts.experiments.FFT.fft_peak_area', 'fft_peak_area'), 
               ('lattice.scripts.experiments.FFT.fft_hv_scan', 'fft_hv_scan'), 
               ('lattice.scripts.experiments.Misc.set_high_volt', 'set_high_volt'), 
               ('lattice.scripts.experiments.Misc.set_linetrigger_offset', 'set_linetrigger_offset'), 
               ('lattice.scripts.experiments.CavityScan.scan_cavity', 'scan_cavity'), 
               ('lattice.scripts.experiments.CavityScan.scan_cavity_397', 'scan_cavity_397'), 
               ('lattice.scripts.experiments.CavityScan.scan_cavity_866', 'scan_cavity_866'), 
               ]

    allowed_concurrent = {
#        'fft_spectrum': ['non_conflicting_experiment'],
#        'non_conflicting_experiment' : ['fft_spectrum'],
    }
    
    launch_history = 1000               
