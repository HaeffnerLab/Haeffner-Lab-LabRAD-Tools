from hardwareConfiguration import channelConfiguration, ddsConfiguration, remoteChannel
 
class user_configuration(object):
    
    #name: (channelNumber, state, on_is_high_ttl)
    ttl_channels = {
                    #external channels
                   '866DP':channelConfiguration(0, False, True),
                   'crystallization':channelConfiguration(1, True, False),
                   'bluePI':channelConfiguration(2, True, False),
                   '110DP':channelConfiguration(3, False, True),
                   'radial':channelConfiguration(4, False, True),
                   'camera':channelConfiguration(5, False, False),
                   #internal channels
                   'DiffCountTrigger':channelConfiguration(16, False, False),
                   'TimetagCount':channelConfiguration(17, False, False),
                   'AdvanceDDS':channelConfiguration(18, False, False),
                   'ResetDDS':channelConfiguration(19,False, False),
                   'ReadoutCount':channelConfiguration(20, False, False),
                   'AdvanceDDS729':channelConfiguration(21, False, False),
                   'ResetDDS729':channelConfiguration(22, False, False),
                   }
    #address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    dds_channels = {
               #local channels
               '866DP':ddsConfiguration(0, (70.0,90.0), (-63.0,-3.0), 80.0, -33.0),
               '110DP':ddsConfiguration(1, (90.0,130.0), (-63.0,-3.0), 110.0, -33.0), 
               'radial':ddsConfiguration(4, (190.0,250.0), (-63.0,-3.0), 220.0, -33.0),
               '854DP':ddsConfiguration(3, (70.0,90.0), (-63.0,-3.0), 80.0, -33.0),
               'pump':ddsConfiguration(5, (90.0,130.0), (-63.0,-10.0), 110.0, -33.0),
               #remote channels
               '729DP':ddsConfiguration(0, (150.0,250.0),  (-63.0,-3.0), 220.0, -33.0, remote = 'pulser_729')
               }
    
    remote_dds_channels = {
                    'pulser_729': remoteChannel('192.168.169.49', 'pulser_729')
                        }