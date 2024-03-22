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
        self.state = True
        self.boardfreqrange = args.get('boardfreqrange', (0.0, 800.0))
        self.boardamplrange = args.get('boardamplrange', (-63.0, -3.0))
        self.boardphaserange = args.get('boardphaserange', (0.0, 360.0))
        self.off_parameters = args.get('off_parameters', (0.0, -63.0))
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
    resetstepDuration = 2 #duration of advanceDDS and resetDDS TTL pulses in units of timesteps
    collectionTimeRange = (0.001, 5.0) #range for normal pmt counting
    sequenceTimeRange = (0.0, 85.0) #range for duration of pulse sequence    
    isProgrammed = False
    sequenceType = None #none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal' #default PMT mode
    collectionTime = {'Normal':0.100,'Differential':0.100} #default counting rates
    okDeviceID = 'Pulser'
    okDeviceFile = 'pulser_2013_06_05.bit'
    lineTriggerLimits = (0, 15000)#values in microseconds 
    secondPMT = True
    DAC = False
    
    #name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {
                  #'adv':channelConfiguration(9, False, False, False, True),
                  #'rst':channelConfiguration(10, False, False, False, True),
                  # '375sw':channelConfiguration(10, False, False, False, False),
                  # hardware out #16 --> config #21 etc. 
                  # 'rst':channelConfiguration(23, False, False, False, False),
                  #'DC multiplexer':channelConfiguration(3, True, False, False, False),
                  'Cold Finger':channelConfiguration(8, True, False, True, False),
                  'Inside Heat Shield':channelConfiguration(7, True, False, True, False),
                  'Cernox':channelConfiguration(6, True, False, True, False),
                  #'C1':channelConfiguration(7, True, False, True, False),
                  #'C2':channelConfiguration(8, True, False, True, False),
                  #'729_1':channelConfiguration(7, True, False, False, False),
                  #'729_2':channelConfiguration(8, True, False, False, False),
                  'bluePI':channelConfiguration(5, False, True, False, False),
                  '422':channelConfiguration(9, True, False, True, False),
                  '375':channelConfiguration(10, True, False, True, False),
                  'awg_on':channelConfiguration(11, False, False, False, True),
                  # 'OvenLaser':channelConfiguration(11, True, False, True, False),
                  '866_diff':channelConfiguration(14, False, True, True, False),
                  # 'camera':channelConfiguration(12, False, False, False, False),
                  'RF_switch':channelConfiguration(6, True, False, True, False),
                  #'397sw':channelConfiguration(11, True, False, True, False),
                  #------------INTERNAL CHANNELS----------------------------------------#
                  #'0':channelConfiguration(0, False, False, False, False),
                  #'1':channelConfiguration(1, False, False, False, False),
                  #'2':channelConfiguration(2, False, False, False, False),
                  #'3':channelConfiguration(3, False, False, False, False),
                  #'4':channelConfiguration(4, False, False, False, False),
                  'DiffCountTrigger':channelConfiguration(16, False, False, False, False),
                  'TimeResolvedCount':channelConfiguration(17, False, False, False, False),
                  'AdvanceDDS':channelConfiguration(18, False, False, False, False),
                  'ResetDDS':channelConfiguration(19, False, False, False, False),
                  'ReadoutCount':channelConfiguration(20, False, False, False, False),
                  'Internal866':channelConfiguration(0, False, False, False, False),
                  'StartExperiment':channelConfiguration(15, True, False, False, False),
                  }
                  
    #address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    ddsDict = {
               '397DP':ddsConfiguration(0, (150.0,250.0), (-63.0,-3.0), 220.0, -63.0,
                                        #boardfreqrange = (170.0,270.0),
                                        #off_parameters = (220.0, -63.0),
                                        #boardphaserange = (0.0, 360.0)
                                         ),
              '397extra':ddsConfiguration(7, (150.0,250.0), (-63.0,-3.0), 200.0, -63.0,
                                        #boardfreqrange = (170.0,270.0),
                                        #off_parameters = (220.0, -63.0),
                                        #boardphaserange = (0.0, 360.0)
                                        ),
                '866DP':ddsConfiguration(6, (50.0,200.0), (-63.0,-3.0), 80.0, -63.0),
                '866extra':ddsConfiguration(3, (50.0,200.0), (-63.0,-3.0), 80.0, -63.0),

                '854DP':ddsConfiguration(2, (70.0,90.0), (-63.0,-3.0), 80.0, -63.0),
                '854extra':ddsConfiguration(5, (70.0,90.0), (-63.0,-3.0), 80.0, -63.0),

                '729local':ddsConfiguration(4, (10.0,280.0), (-63.0,-3.0), 220.0, -63.0,),
                '729extra':ddsConfiguration(1, (10.0,280.0), (-63.0,-3.0), 220.0, -63.0,),

                 #'729DP':ddsConfiguration(2, (150.0,250.0), (-63.0,-3.0), 220.0, -63.0,),
                #remote channels
                #'729DP':ddsConfiguration(0, (150.0,250.0),  (-63.0,-3.0), 220.0, -33.0, remote = 'pulser_729')
               }

    remoteChannels = {
                    }
