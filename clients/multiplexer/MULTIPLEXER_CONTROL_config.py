class multiplexer_control_config(object):
    '''
    configuration file for multiplexer client
    info is the configuration dictionary in the form
    {channel_name: (hint, display_location)), }
    '''
    info = {'866': ('346.00002', (0,1)),
            '422': ('354.53919', (0,0)),
            '397 Single Pass': ('377.61131', (1,0)),
            '729': ('411.04243', (2,1)),
            '397 diode': ('755.22262', (2,0)),
            '854': ('350.86275', (1,1)),
            '397 lattice room': ('', (3,0))
            }