class channelConfiguration(object):
    """
    Stores complete configuration for each of the channels
    """
    def __init__(self, channelNumber, ismanual, manualstate,  manualinversion, autoinversion):
        self.channelnumber = channelNumber
        self.ismanual = ismanual
        self.manualstate = manualstate
        self.manualinv = manualinversion
        self.autoinv = autoinversion
        
class ddsConfiguration(object):
    """
    Stores complete configuration of each DDS board
    """
    def __init__(self, address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
        self.channelnumber = address
        self.allowedfreqrange = allowedfreqrange
        self.allowedamplrange = allowedamplrange
        self.frequency = frequency
        self.amplitude = amplitude
        self.t1 = 4000
        self.t2 = 4000
        self.time_step = 4
        self.lattice_parameter = [4000,4000,4]
        self.state = True
        self.boardfreqrange = args.get('boardfreqrange', (0.0, 1500.0))
        self.boardramprange = args.get('boardramprange', (0.000113687, 7.4505806))
        self.board_amp_ramp_range = args.get('board_amp_ramp_range', (0.00174623, 22.8896))
        self.boardamplrange = args.get('boardamplrange', (-37.0, 17.0))
        self.boardphaserange = args.get('boardphaserange', (0.0, 360.0))
        self.off_parameters = args.get('off_parameters', (0.0, -37.0))
        self.phase_coherent_model = args.get('phase_coherent_model', True)        
        self.remote = args.get('remote', False)
        self.name = None #will get assigned automatically

class remoteChannel(object):
    def __init__(self, ip, server, **args):
        self.ip = ip
        self.server = server
        self.reset = args.get('reset', 'reset_dds')
        self.program = args.get('program', 'program_dds')
        
class hardwareConfiguration(object):
    channelTotal = 32
    timeResolution = '40.0e-9' #seconds
    timeResolvedResolution = 10.0e-9
    maxSwitches = 1022
    resetstepDuration = 3 #duration of advanceDDS and resetDDS TTL pulses in units of timesteps
    collectionTimeRange = (0.010, 5.0) #range for normal pmt counting
    sequenceTimeRange = (0.0, 85.0) #range for duration of pulse sequence    
    isProgrammed = False
    sequenceType = None #none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal' #default PMT mode
    collectionTime = {'Normal':0.100,'Differential':0.100} #default counting rates
    okDeviceID = 'Pulser2'
    #okDeviceFile = 'photon_2015_06_10.bit'
    okDeviceFile = 'photon_2015_7_13.bit'
    lineTriggerLimits = (0, 15000)#values in microseconds 
    secondPMT = False
    DAC = False
    
    #name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {
                   'ttl_0':channelConfiguration(0, False, False, False, False), ## camera
                   'sMOT_PROBE':channelConfiguration(1, False, False, False, False),
                   'sMOT_PROBE_SPIN':channelConfiguration(2, False, False, False, False),
                   'BIG_MOT_SH':channelConfiguration(3, False, False, True, True),
                   'sMOT_AO':channelConfiguration(4, False, False, False, False),
                   'BIG_MOT_AO':channelConfiguration(5, False, True, False, False),
                   '405_ECDL':channelConfiguration(6, False, False, False, False),
                   '405_Raman':channelConfiguration(7, False, False, False, False),
                   '435_Raman':channelConfiguration(8, False, False, False, False),
                   '266_SB':channelConfiguration(9, False, False, False, False),
                   'SP1':channelConfiguration(10, False, False, False, False),
                   'SP2':channelConfiguration(11, False, False, False, False),
                   'AdvanceDDS':channelConfiguration(18, False, False, False, False),
                   'ResetDDS':channelConfiguration(19, False, False, False, False),
                   'AO1':channelConfiguration(20, False, False, False, False), ### triggering for analog board
                   'AO2':channelConfiguration(21, False, False, False, False), ### triggering for analog board
                   'B_x_sign':channelConfiguration(21, True, False, False, False), 
                   'B_y_sign':channelConfiguration(22, True, True, False, False),
                   'B_z_sign':channelConfiguration(23, True, True, False, False), 
                   'dummy_clock':channelConfiguration(24, False, False, False, False), ## for plotting the clock purpose only 
                   
                }
    #address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    ddsDict =   {
                'DDS_0':ddsConfiguration(    0,  (0.1,41.0),   (-37.0,-10.0),  40.0,   -36.0),
#                  'DDS_1':ddsConfiguration(    1,  (0.1,300.0),   (-37.0,17.0),  41.0,   10.0),
#                  'DDS_2':ddsConfiguration(    2,  (0.1,300.0),   (-37.0,17.0),  42.0,   10.0),
#                  'DDS_3':ddsConfiguration(    3,  (0.1,300.0),   (-37.0,17.0),  43.0,   10.0),
#                  'DDS_4':ddsConfiguration(    4,  (40.0,300.0),   (-37.0,17.0),  44.0,   10.0),
#                  'DDS_5':ddsConfiguration(    5,  (40.0,300.0),   (-37.0,17.0),  45.0,   10.0),
#                 'DDS_6':ddsConfiguration(    6,  (40.0,300.0),   (-37.0,17.0),  46.0,   10.0),
#                'Moving Lattice':ddsConfiguration(    7,  (40.0,300.0),   (-37.0,17.0),  47.0,   0.0),
#                 'DDS_8':ddsConfiguration(    8,  (40.0,300.0),   (-37.0,17.0),  58.0,   -36.0),
#                 'DDS_9':ddsConfiguration(    9,  (40.0,300.0),   (-37.0,17.0),  59.0,   -36.0),
#                'DDS_10':ddsConfiguration(    10,  (0.0,200.0),   (-37.0,0),  120.0,   -37.0),
#                'DDS_11':ddsConfiguration(    11,  (0.0,200.0),   (-37.0,0),  120.0,   -37.0),
#                'DDS_12':ddsConfiguration(    12,  (0.0,200.0),   (-37.0,0),  120.0,   -37.0),
#                'DDS_13':ddsConfiguration(    13,  (0.0,200.0),   (-37.0,0),  120.0,   -37.0),
#                'DDS_14':ddsConfiguration(    14,  (0.0,200.0),   (-37.0,0),  120.0,   -37.0),
#                'DDS_15':ddsConfiguration(    15,  (0.0,200.0),   (-37.0,0),  120.0,   -37.0),

                }
    remoteChannels = {
                    }