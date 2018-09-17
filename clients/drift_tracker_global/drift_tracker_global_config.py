class config_729_tracker(object):
    
    ID = 99992
    
    update_rate = 10.0 #seconds
    frequency_limit = (-60, 140) #MHz
    saved_lines_729 = ['729Experiments','saved_lines_729']
    favorites = {'S+1/2D-3/2':'OP', 'S-1/2D+3/2':'Right OP', 'S-1/2D-5/2':'carrier -1/2-5/2', 'S-1/2D-1/2':'carrier -1/2-1/2'}
    initial_selection = ['S-1/2D-5/2', 'S-1/2D-1/2'] # select these lines in the entry table at startup, has to be the name that is saved, i.e. instead of OP, S+1/2D-3/2
    initial_values = [-33.5, -20.8] # initial frequencies of the lines at startup (in MHz)

    default_color_cycle = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    show_rate = 1

    save_folder = ['', 'Drift_Tracking', 'Cavity729']
    dataset_name = 'Cavity Drift'


