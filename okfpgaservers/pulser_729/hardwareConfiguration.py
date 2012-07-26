class ddsConfiguration():
    """
    Stores complete configuration of each DDS board
    """
    def __init__(self, address, boardfreqrange, allowedfreqrange, boardamplrange, allowedamplrange, boardphaserange,frequency, amplitude):
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
        self.boardphaserange = boardphaserange
        self.frequency = frequency
        self.amplitude = amplitude
        
class hardwareConfiguration():
    ddsChannelTotal = 1
    timeResolution = 40.0e-9 #seconds
    okDeviceID = 'Pulser729'
    okDeviceFile = 'photon.bit'
    #don't exceed 400 =  boardfreqrangemax / 2.0 for the allowed range
    ddsDict = {
               '729DP':ddsConfiguration(0, (0.0, 800.0), (190.0,250.0), (-63.0,-3.0), (-63.0,-3.0), (0.0,360.0), 220.0, -63.0)
               }