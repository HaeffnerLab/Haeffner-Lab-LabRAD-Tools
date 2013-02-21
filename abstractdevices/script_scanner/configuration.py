class config(object):

    #list in the format (import_path, class_name)
    scripts = [
               ('sample_experiment', 'sample_experiment'), 
               ('sample_experiment', 'conflicting_experiment'),
               ('sample_experiment', 'non_conflicting_experiment'),
               ('sample_experiment', 'crashing_example'), 
               ]

    #experiments are allowed to run together
    allowed_concurrent = {
        'sample_experiment': ['non_conflicting_experiment'],
        'non_conflicting_experiment' : ['sample_experiment'],
    }
    
    launch_history = 1000               
