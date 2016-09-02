class config_729_tracker(object):
    
    ID = 99992
    
    update_rate = 10.0 #seconds
    frequency_limit = (-60, 140) #MHz
    saved_lines_729 = ['729Experiments','saved_lines_729']
    favorites = {'S+1/2D-3/2':'OP', 'S-1/2D+3/2':'Right OP', 'S-1/2D-5/2':'carrier -1/2-5/2', 'S-1/2D-1/2':'carrier -1/2-1/2'}
    initial_selection = ['S-1/2D-1/2', 'S-1/2D-5/2'] # select these lines in the entry table at startup, has to be the name that is saved, i.e. instead of OP, S+1/2D-3/2
    initial_values = [-19.8033, -30.2511] # initial frequencies of the lines at startup (in MHz)


