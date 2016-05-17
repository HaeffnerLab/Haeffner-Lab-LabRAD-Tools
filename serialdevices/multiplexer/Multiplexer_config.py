class multiplexer_config(object):
    '''
    configuration for the multiplexer channels
    contains dictionary info in the form of
    {channel_name: (channel_number, wavelength),.. }
    '''
    info = {'422': (4, '422'),
            '866': (6, '866'),
            #'397 Offset': (8, '397'),
            '729': (10, '729'),
            '397 diode': (11, '397'),
            '854': (5, '854'),   
            #'397 lattice room': (3, '397 lattice room'),
            #'397 injected' (1, '397')
            '794':(1,'794'),
			'794 Pro':(2,'794'),
            '729 inject':(3, '729')
            }
        
