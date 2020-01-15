class channelConfiguration(object):
    """
    Stores complete information for each DAC channel
    """


    def __init__(self, dacChannelNumber, trapElectrodeNumber = None, smaOutNumber = None, name = None, boardVoltageRange = (-10, 10), allowedVoltageRange = (-10, 10)):
        self.dacChannelNumber = dacChannelNumber
        self.trapElectrodeNumber = trapElectrodeNumber
        self.smaOutNumber = smaOutNumber
        self.boardVoltageRange = boardVoltageRange
        self.allowedVoltageRange = allowedVoltageRange
        if (name == None) & (trapElectrodeNumber != None):
            self.name = str(trapElectrodeNumber).zfill(2)
        else:
            self.name = name

    def computeDigitalVoltage(self, analogVoltage):
        return int(round(sum([ self.calibration[n] * analogVoltage ** n for n in range(len(self.calibration)) ])))



class hardwareConfiguration(object): 
    EXPNAME = 'Spacetime'
    default_multipoles = ['Ex', 'Ey','Ez','U1','U3']
    # okDeviceID = 'DAC Controller' #for old DAC (v4)
    okDeviceID = 'stdac_v5' #for spacetime DAC V5
    # okDeviceFile = 'control_noninverted.bit' #for old DAC (v4)
    okDeviceFile = 'dac.bit' #for new DAC (v5)
    centerElectrode = False #write False if no Centerelectrode
    PREC_BITS = 16
    pulseTriggered = True
    maxCache = 126
    filter_RC = 5e4 * 4e-7
    
    elec_dict = {      

###################################### SPACETIME CONFIGURATION
        '01': channelConfiguration(6, trapElectrodeNumber=1),#
        '02': channelConfiguration(9, trapElectrodeNumber=2),# 
        '03': channelConfiguration(7, trapElectrodeNumber=3),# w
        '04': channelConfiguration(4, trapElectrodeNumber=4),# w
        '05': channelConfiguration(5, trapElectrodeNumber=5),# w
        '06': channelConfiguration(8, trapElectrodeNumber=6),#
        '07': channelConfiguration(11, trapElectrodeNumber=7),# w
        '08': channelConfiguration(10, trapElectrodeNumber=8), # w
        '09': channelConfiguration(3, trapElectrodeNumber=9),#####
###############################

        # # For testing all channels
        # '1': channelConfiguration(1, trapElectrodeNumber=1), #
        # '2': channelConfiguration(2, trapElectrodeNumber=2),#
        # '3': channelConfiguration(3, trapElectrodeNumber=3),#
        # '4': channelConfiguration(4, trapElectrodeNumber=4),#
        # '5': channelConfiguration(5, trapElectrodeNumber=5),#
        # '6': channelConfiguration(6, trapElectrodeNumber=6),#
        # '7': channelConfiguration(7, trapElectrodeNumber=7),#
        # '8': channelConfiguration(8, trapElectrodeNumber=8),#
        # '9': channelConfiguration(9, trapElectrodeNumber=9),#
        # '10': channelConfiguration(10, trapElectrodeNumber=10),# 
        # '11': channelConfiguration(11, trapElectrodeNumber=11), #
        # '12': channelConfiguration(12, trapElectrodeNumber=12),#
        # '13': channelConfiguration(13, trapElectrodeNumber=13),#
        # '14': channelConfiguration(14, trapElectrodeNumber=14),#
        # '15': channelConfiguration(15, trapElectrodeNumber=15),#
        # '16': channelConfiguration(16, trapElectrodeNumber=16),#
        # '17': channelConfiguration(17, trapElectrodeNumber=17),#
        # '18': channelConfiguration(18, trapElectrodeNumber=18),#
        # '19': channelConfiguration(19, trapElectrodeNumber=19),#
        # '20': channelConfiguration(20, trapElectrodeNumber=20),#
        # '21': channelConfiguration(21, trapElectrodeNumber=21),#
        # '22': channelConfiguration(22, trapElectrodeNumber=22),
        # '23': channelConfiguration(23, trapElectrodeNumber=23), 
        # '24': channelConfiguration(24, trapElectrodeNumber=24),
        # '25': channelConfiguration(25, trapElectrodeNumber=25),
        # '26': channelConfiguration(26, trapElectrodeNumber=26),
        # '27': channelConfiguration(27, trapElectrodeNumber=27),
        # '28': channelConfiguration(28, trapElectrodeNumber=28) 

        #For using old Lattice DAC, 2018-10-19
        # '01': channelConfiguration(10, trapElectrodeNumber=1),
        # '02': channelConfiguration(5, trapElectrodeNumber=2),
        # '03': channelConfiguration(9, trapElectrodeNumber=3),
        # '04': channelConfiguration(13, trapElectrodeNumber=4),
        # '05': channelConfiguration(11, trapElectrodeNumber=5),
        # '06': channelConfiguration(6, trapElectrodeNumber=6),
        # '07': channelConfiguration(3, trapElectrodeNumber=7),
        # '08': channelConfiguration(1, trapElectrodeNumber=8),
        # '09': channelConfiguration(16, trapElectrodeNumber=9),#####
        }

    notused_dict = {
               }

    sma_dict = {
        'RF bias': channelConfiguration(2, smaOutNumber=1, name='RF bias', boardVoltageRange=(-10., 10.), allowedVoltageRange=(-10, 10)),
      #  'Test FPGA 1':channelConfiguration(13, smaOutNumber=2, name='Test FPGA 1', boardVoltageRange=(-10., 10.), allowedVoltageRange=(-10.0, 10)),
        # 'Test FPGA 2':channelConfiguration(25, smaOutNumber=3, name='Test FPGA 2', boardVoltageRange=(-10., 10.), allowedVoltageRange=(-10.0, 10))

        }
    
####SQUIP DAC CONFIG
#    elec_dict = {
#        '01': channelConfiguration(7, trapElectrodeNumber=1),#
#        '02': channelConfiguration(4, trapElectrodeNumber=2),# 
#        '03': channelConfiguration(6, trapElectrodeNumber=3),#
#        '04': channelConfiguration(9, trapElectrodeNumber=4),#
#        '05': channelConfiguration(8, trapElectrodeNumber=5),#
#        '06': channelConfiguration(5, trapElectrodeNumber=6),#
#        '07': channelConfiguration(3, trapElectrodeNumber=7),#
#        '08': channelConfiguration(2, trapElectrodeNumber=8), #
#        '09': channelConfiguration(10, trapElectrodeNumber=9),#####
#        '10': channelConfiguration(11, trapElectrodeNumber=10),# need to check if 13 works
#        '11': channelConfiguration(12, trapElectrodeNumber=11), #
#        '12': channelConfiguration(13, trapElectrodeNumber=12),#
#        '13': channelConfiguration(14, trapElectrodeNumber=13),#
#        '14': channelConfiguration(15, trapElectrodeNumber=14),#
#        '15': channelConfiguration(16, trapElectrodeNumber=15),#
#        '16': channelConfiguration(17, trapElectrodeNumber=16),#
#        '17': channelConfiguration(18, trapElectrodeNumber=17),#
#        '18': channelConfiguration(19, trapElectrodeNumber=18),#
#        '19': channelConfiguration(20, trapElectrodeNumber=19),#
#        '20': channelConfiguration(21,  trapElectrodeNumber=20),#
#        '21': channelConfiguration(22 	, trapElectrodeNumber=21),#
#        '22': channelConfiguration(23, trapElectrodeNumber=22),
#        '23': channelConfiguration(24, trapElectrodeNumber=23), 
#        '24': channelConfiguration(25, trapElectrodeNumber=24),
#        '25': channelConfiguration(26, trapElectrodeNumber=25),
#        '26': channelConfiguration(27,  trapElectrodeNumber=26),
#        '27': channelConfiguration(28, trapElectrodeNumber=27),
#        '28': channelConfiguration(29, trapElectrodeNumber=28) 
#        }

#    notused_dict = {
#               }

#    sma_dict = {
#        'RF bias': channelConfiguration(11, smaOutNumber=1, name='RF bias', boardVoltageRange=(-10., 10.), allowedVoltageRange=(-10, 10)),
#      #  'Test FPGA 1':channelConfiguration(13, smaOutNumber=2, name='Test FPGA 1', boardVoltageRange=(-10., 10.), allowedVoltageRange=(-10.0, 10)),
#        'Test FPGA 2':channelConfiguration(25, smaOutNumber=3, name='Test FPGA 2', boardVoltageRange=(-10., 10.), allowedVoltageRange=(-10.0, 10))


#        }
