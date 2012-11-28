class config(object):
    
    double_pass_passes = 2
    double_pass_direction = -1 #1 means add frequencies, -1 subtracts
    
    fit_order = 2 #order of polynomial for fitting
    
    keep_measurements = 24 * 3600 #seconds, how long to keep measurements
    
    #data vault saving configuration
    save_folder = ['', 'Drfit Tracking', 'Cavity729']
    dataset_name = 'Cavity Drift'
    #signaling
    signal_id = 9898991