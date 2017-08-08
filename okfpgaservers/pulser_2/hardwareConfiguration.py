class channelConfiguration(object):
    """
    Stores complete configuration for each of the channels
    """
    def __init__(self, channelNumber, state, on_is_high):
        self.channelnumber = channelNumber
        self.state = state
        self.on_is_high = on_is_high
        
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
        self.boardfreqrange = (0.0, 800.0)
        self.boardamplrange = (-63.0, -3.0)
        self.boardphaserange = (0.0, 360.0)
        self.allowedphaserange = self.boardphaserange
        self.off_amplitude = -63.0#dBm
        self.remote = args.get('remote', False)
        self.inSequenceUse = False

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
    maxSwitches = 16382
    max_dds_edges = 1024
    resetstepDuration = 2 #duration of advanceDDS and resetDDS TTL pulses in units of timesteps
    collectionTimeRange = (0.010, 5.0) #range for normal pmt counting
    max_pulse_duration = 2125000000 #range for duration of pulse sequence, timesteps 
    isProgrammed = False
    sequenceType = None #none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal' #default PMT mode
    collectionTime = {'Normal':0.100,'Differential':0.100} #default counting rates
    okDeviceID = 'Pulser2'
    okDeviceFile = 'pulser.bit'
    lineTriggerLimits = (0, 15000)#values in microseconds 
    secondPMT = False
    DAC = False