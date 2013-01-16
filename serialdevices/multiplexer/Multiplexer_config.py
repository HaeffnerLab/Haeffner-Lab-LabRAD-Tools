class multiplexer_config(object):
    '''
    configuration for the multiplexer channels
    contains dictionary info in the form of
    {channel_name: (channel_number, wavelength),.. }
    '''
    info = {'422': (4, '422'),
            '866': (6, '866'),
            '397 Single Pass': (5, '397'),
            '729': (10, '729'),
            '397 diode': (2, '397'),
            '854': (12, '854'),   
            '397 lattice room': (1, '397')
            #'397 injected' (1, '397')
            #'732':(3,'732')
            }
        