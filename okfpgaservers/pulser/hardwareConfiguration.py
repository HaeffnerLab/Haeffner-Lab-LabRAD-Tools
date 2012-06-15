class channelConfiguration():
    """
    Stores complete configuration for each of the channels
    """
    def __init__(self, channelNumber, ismanual, manualstate,  manualinversion, autoinversion):
        self.channelnumber = channelNumber
        self.ismanual = ismanual
        self.manualstate = manualstate
        self.manualinv = manualinversion
        self.autoinv = autoinversion
    
class ddsConfiguration():
    """
    Stores complete configuration of each DDS board
    """
    def __init__(self, address, boardfreqrange, allowedfreqrange, boardamplrange, allowedamplrange, frequency = None, amplitude = None):
        '''
        address is the hardware address
        board settings refer to the DIP settings on the board
        allowed settings are allowed to be set by the user
        frequencies are in MHz
        amplitudes are in dBm
        
        frequency and amplitude provide optional initialization parameters
        '''
        self.channelnumber = address
        self.boardfreqrange = boardfreqrange
        self.allowedfreqrange = allowedfreqrange
        self.boardamplrange = boardamplrange
        self.allowedamplrange = allowedamplrange
        self.frequency = frequency
        self.amplitude = amplitude
        
class hardwareConfiguration():
    channelTotal = 32
    ddsChannelTotal = 8
    timeResolution = 40.0e-9 #seconds
    timeResolvedResolution = timeResolution/4.0
    maxSwitches = 1022
    isProgrammed = False
    sequenceType = None #none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal' #default PMT mode
    collectionTime = {'Normal':0.100,'Differential':0.100} #default counting rates
    
    #name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {
                   '866DP':channelConfiguration(0, False, True, True, False),
                   'crystallization':channelConfiguration(1, True, False, False, False),
                   'bluePI':channelConfiguration(2, True, False, True, False),
                   '110DP':channelConfiguration(3, False, True, True, False),
                   'axial':channelConfiguration(4, False, True, True, True),
                   'camera':channelConfiguration(5, False, False, True, True),
                   #future channels
                   '729DP':channelConfiguration(10, False, True, True, False),
                   '854DP':channelConfiguration(11, False, True, True, False),
                   #------------INTERNAL CHANNELS----------------------------------------#
                   'DiffCountTrigger':channelConfiguration(16, False, False, False, False),
                   'TimeResolvedCount':channelConfiguration(17, False, False, False, False),
                   'AdvanceDDS':channelConfiguration(18, False, False, False, False),
                   'ResetDDS':channelConfiguration(19, False, False, False, False)
                   }
    
    ddsDict = {
#               '866DP':ddsConfiguration(0, (30.0,130.0), (70.0,90.0), (-63.0,-3.0), (-63.0,-3.0), 80.0, -33.0),
#               '110DP':ddsConfiguration(1, (60.0,160.0), (90.0,130.0), (-63.0,-3.0), (-63.0,-3.0), 110.0, -33.0),
#               'axial':ddsConfiguration(2, (170.0,270.0), (190.0,250.0), (-63.0,-3.0), (-63.0,-3.0), 220.0, -33.0),
               
               '866DP':ddsConfiguration(0, (30.0,130.0), (30.0,130.0), (-63.0,-3.0), (-63.0,-3.0), 80.0, -33.0),
               '110DP':ddsConfiguration(1, (30.0,130.0), (30.0,130.0), (-63.0,-3.0), (-63.0,-3.0), 90.0, -33.0),
               'axial':ddsConfiguration(2, (30.0,130.0), (30.0,130.0), (-63.0,-3.0), (-63.0,-3.0), 100.0, -33.0),
               '854DP':ddsConfiguration(3, (30.0,130.0), (70.0,130.0), (-63.0,-3.0), (-63.0,-3.0), 105.0, -33.0),
               }