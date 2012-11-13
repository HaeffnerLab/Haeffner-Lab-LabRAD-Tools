class config_729_hist(object):
    #IDs for signaling
    ID_A = 99999
    ID_B = 99998
    #data vault comment
    dv_parameter = 'Histogram729'
    #semaphore locations
    readout_threshold_dir =  ['729Experiments','readout_threshold']

class state_readout(object):
    #IDs for signaling
    ID = 99993
    
    readout_threshold_dir =  ['729Experiments','readout_threshold']
    readout_time_dir = ['729Experiments','state_readout_duration']
    
    repeat_each_measurement = ['729Experiments','repeat_each_measurement']
    
    state_readout_frequency_397 = ['729Experiments','state_readout_frequency_397']
    state_readout_amplitude_397 = ['729Experiments','state_readout_amplitude_397']
    state_readout_frequency_866 = ['frequency_866']
    state_readout_amplitude_866 = ['729Experiments','state_readout_amplitude_866']

class config_729_spectrum(object):
    #IDs for signaling
    ID = 99996
    #spectrum
    spectrum_excitation_time = ['729Experiments','Spectrum','excitation_time']
    spectrum_frequencies = ['729Experiments','Spectrum','frequencies']
    spectrum_amplitude_729 = ['729Experiments','Spectrum','spectrum_amplitude_729']
    spectrum_use_saved = ['729Experiments','Spectrum','spectrum_use_saved_frequency']
    spectrum_saved_freq = ['729Experiments','Spectrum','spectrum_saved_frequency']
    #rabi flop
    saved_lines_729 = ['729Experiments','saved_lines_729']
    
    rabi_frequency = ['729Experiments','RabiFlopping','frequency']
    rabi_excitation_times = ['729Experiments','RabiFlopping','excitation_times']
    rabi_amplitude_729 = ['729Experiments','RabiFlopping','rabi_amplitude_729']
    rabi_use_saved = ['729Experiments','RabiFlopping','rabi_flopping_use_saved_frequency']
    rabi_saved_freq = ['729Experiments','RabiFlopping','rabi_flopping_saved_frequency']
    #saved freq
    line_parameter_names = ['Name', 'Center', 'Scan Span','Scan Resolution','Scan Amplitude', 'Scan Excitation Duration']
    line_parameter_units = ['MHz', 'kHz', 'kHz', 'dBm', 'us']
    line_parameter_sig_figs = [4, 2, 2 , 1 , 1]
    saved_lines_729 = ['729Experiments','saved_lines_729']

class config_729_state_preparation(object):
    #IDs for signaling
    ID = 99994
    #repump d5/2
    repump_d_duration = ['729Experiments','repump_d_duration']
    repump_d_frequency_854 = ['frequency_854']
    repump_d_amplitude_854 = ['729Experiments','repump_d_amplitude_854']
    #doppler cooling
    doppler_cooling_frequency_397 = ['doppler_cooling_frequency_397']
    doppler_cooling_frequency_866 = ['frequency_866']
    doppler_cooling_amplitude_397 = ['doppler_cooling_amplitude_397']
    doppler_cooling_amplitude_866 = ['doppler_cooling_amplitude_866']
    doppler_cooling_duration = ['doppler_cooling_duration']
    doppler_cooling_repump_additional = ['doppler_cooling_repump_additional']
    #optical pumping
    optical_pumping_enable = ['729Experiments','optical_pumping_enable']
    optical_pumping_frequency_729 = ['729Experiments','optical_pumping_user_selected_frequency_729']
    optical_pumping_amplitude_729 = ['729Experiments','optical_pumping_amplitude_729']
    optical_pumping_frequency_854 = ['frequency_854']
    optical_pumping_amplitude_854 = ['729Experiments','optical_pumping_amplitude_854']
    optical_pumping_frequency_866 = ['frequency_866']
    optical_pumping_amplitude_866 = ['729Experiments','optical_pumping_amplitude_866']
    optical_pumping_continuous = ['729Experiments','optical_pumping_continuous']
    optical_pumping_pulsed = ['729Experiments','optical_pumping_pulsed']
    optical_pumping_continuous_duration = ['729Experiments','optical_pumping_continuous_duration']
    optical_pumping_continuous_pump_additional = ['729Experiments','optical_pumping_continuous_repump_additional']
    optical_pumping_pulsed_cycles = ['729Experiments','optical_pumping_pulsed_cycles']
    optical_pumping_pulsed_duration_729 = ['729Experiments','optical_pumping_pulsed_duration_729']
    optical_pumping_pulsed_duration_repumps = ['729Experiments','optical_pumping_pulsed_duration_repumps']
    optical_pumping_pulsed_duration_additional_866 = ['729Experiments','optical_pumping_pulsed_duration_additional_866']
    optical_pumping_pulsed_duration_between_pulses = ['729Experiments','optical_pumping_pulsed_duration_between_pulses']
    optical_pumping_use_saved = ['729Experiments','optical_pumping_use_saved']
    optical_pumping_use_saved_line =  ['729Experiments','optical_pumping_use_saved_line']
    saved_lines_729 = ['729Experiments','saved_lines_729']
    #heating
    background_heating_duration = ['729Experiments','background_heating_time']
    line_parameter_units = ['MHz', 'kHz', 'kHz', 'dBm', 'us']

class config_729_tracker(object):
    
    ID = 99992
    
    frequency_limit = (150, 250) #MHz
    saved_lines_729 = ['729Experiments','saved_lines_729']