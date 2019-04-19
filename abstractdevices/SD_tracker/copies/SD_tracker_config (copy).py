class config(object):
    
    double_pass_passes = 2
    double_pass_direction = -1 #1 means add frequencies, -1 subtracts
    
    fit_order = 1 #order of polynomial for fitting
    
    keep_line_center_measurements = 24 * 3600
    keep_B_measurements = 0.5*3600 #seconds
    
    #data vault saving configuration
    save_folder = ['', 'Drift_Tracking', 'Cavity729']
    dataset_name = 'Cavity Drift'
    #signaling
    signal_id = 9898991