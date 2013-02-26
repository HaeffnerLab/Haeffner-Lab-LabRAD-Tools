class configuration(object):

    freq_866 = set([
                    ('Fixed Parameters', 'frequency_866'),
                    ('Doppler Cooling', 'doppler_cooling_frequency_866'),
                    ('OpticalPumping','optical_pumping_frequency_866')
                    ])
    
    freq_854 = set([
                    ('Fixed Parameters', 'frequency_854'),
                    ('OpticalPumping', 'optical_pumping_frequency_854'),
                    ('RepumpD_5_2', 'repump_d_frequency_854')
                    ])
                   
    matched_parameters = [
                          freq_866,
                          freq_854,
                          ]