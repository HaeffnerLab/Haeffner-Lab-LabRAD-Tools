class channelConfiguration(object):
    """
    Stores complete information for each DAC channel
    """


    def __init__(self, dacChannelNumber, trapElectrodeNumber = None, smaOutNumber = None, name = None, boardVoltageRange = (-10, 10), allowedVoltageRange = (0.0, 10.0)):
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
    EXPNAME = 'Laserroom'
    default_multipoles = ['Ex', 'Ey', 'Ez', 'U1', 'U2', 'U3']
    okDeviceID = 'laserdac'
    okDeviceFile = 'dac.bit'
    centerElectrode = False #write False if no Centerelectrode
    PREC_BITS = 16
    pulseTriggered = True
    maxCache = 126
    filter_RC = 5e4 * 4e-7
    channel_name_dict = {
            '01' : '397',
            '02' : '866',
            '03' : '422',
            '04' : '854',
            '05' : '729supervisor',
            '06' : '729slave'
            }
    elec_dict = {
        '01': channelConfiguration(1, trapElectrodeNumber=1),
        '02': channelConfiguration(2, trapElectrodeNumber=2),
        '03': channelConfiguration(3, trapElectrodeNumber=3),
        '04': channelConfiguration(4, trapElectrodeNumber=4),
        '05': channelConfiguration(5, trapElectrodeNumber=5),
        '06': channelConfiguration(6, trapElectrodeNumber=6),
        #'07': channelConfiguration(7, trapElectrodeNumber=7),
        #'08': channelConfiguration(8, trapElectrodeNumber=8),
        #'09': channelConfiguration(9, trapElectrodeNumber=9),
        #'10': channelConfiguration(10, trapElectrodeNumber=10),
        #'11': channelConfiguration(11, trapElectrodeNumber=11),
        #'12': channelConfiguration(12, trapElectrodeNumber=12),
        #'13': channelConfiguration(13, trapElectrodeNumber=13),
        #'14': channelConfiguration(14, trapElectrodeNumber=14),
        #'15': channelConfiguration(15, trapElectrodeNumber=15),
        #'16': channelConfiguration(16, trapElectrodeNumber=16),
        #'17': channelConfiguration(17, trapElectrodeNumber=17),
        #'18': channelConfiguration(18, trapElectrodeNumber=18),
        #'19': channelConfiguration(19, trapElectrodeNumber=19),
        #'20': channelConfiguration(20, trapElectrodeNumber=20),
        #'21': channelConfiguration(21, trapElectrodeNumber=21),
        #'22': channelConfiguration(22, trapElectrodeNumber=22),
        #'23': channelConfiguration(23, trapElectrodeNumber=23)
        }

    notused_dict = {
        #'24': channelConfiguration(2, trapElectrodeNumber=24),
        #'25': channelConfiguration(3, trapElectrodeNumber=25),
        #'26': channelConfiguration(4, trapElectrodeNumber=26),
        #'27': channelConfiguration(16, trapElectrodeNumber=27),
        #'28': channelConfiguration(22, trapElectrodeNumber=28)
               }

    sma_dict = {
        #'RF bias': channelConfiguration(1, smaOutNumber=1, name='RF bias', boardVoltageRange=(-40., 40.), allowedVoltageRange=(-2.0, 0))
        }
