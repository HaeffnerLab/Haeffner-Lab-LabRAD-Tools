class config(object):

    #list in the format (import_path, class_name)
    scripts = [
               ('lattice.scripts.experiments.FFT.fft_spectrum', 'fft_spectrum'), 
               ('lattice.scripts.experiments.FFT.fft_peak_area', 'fft_peak_area'), 
               ('lattice.scripts.experiments.FFT.fft_hv_scan', 'fft_hv_scan'), 
#               ('sample_experiment', 'non_conflicting_experiment'),
#               ('sample_experiment', 'crashing_example'), 
               ]

    #experiments are allowed to run together
    allowed_concurrent = {
#        'fft_spectrum': ['non_conflicting_experiment'],
#        'non_conflicting_experiment' : ['fft_spectrum'],
    }
    
    launch_history = 1000               
