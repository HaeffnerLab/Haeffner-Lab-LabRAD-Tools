class config(object):
    
    double_pass_passes = 2
    double_pass_direction = -1 #1 means add frequencies, -1 subtracts
    
    fit_order = 1 #order of polynomial for fitting
    
    default_keep_line_center_measurements_local = 100*60
    default_keep_line_center_measurements_global = 100*60
    default_keep_B_measurements_local = 100*60
    auto_update_rate = 10 #'s'
    clear_all_duration = 7*24*60*60
    
    #data vault saving configuration
    save_folder = ['', 'Drift_Tracking', 'Cavity729']
    dataset_name = 'Cavity Drift'
    #signaling
    signal_id = 9898991
