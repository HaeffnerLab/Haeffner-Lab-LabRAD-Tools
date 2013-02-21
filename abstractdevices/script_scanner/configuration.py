class config(object):

    #list in the format (import_path, class_name)
    scripts = [
               ('sample_experiment', 'fft_spectrum'), 
               ('sample_experiment', 'conflicting_experiment'),
               ('sample_experiment', 'non_conflicting_experiment'),
               ('sample_experiment', 'crashing_example'), 
               ]

    #experiments are allowed to run together
    allowed_concurrent = {
        'fft_spectrum': ['non_conflicting_experiment'],
        'non_conflicting_experiment' : ['fft_spectrum'],
    }
    
    launch_history = 1000               
