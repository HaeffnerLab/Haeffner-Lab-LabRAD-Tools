class channelConfiguration(object):
    """
    Stores complete information for each DAC channel
    """


    def __init__(self, dacChannelNumber, trapElectrodeNumber = None, smaOutNumber = None, name = None, boardVoltageRange = (-40, 40), allowedVoltageRange = (-35, 35)):
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
    EXPNAME = 'CCT'
    defaultMultipoles = ['Ex', 'Ey', 'Ez', 'U1', 'U2', 'U3']
    okDeviceID = 'DAC Controller'
    okDeviceFile = 'control_nonnoninverted.bit'
    centerElectrode = 23
    PREC_BITS = 16
    pulseTriggered = True
    maxCache = 126
    elecDict = {
        '01': channelConfiguration(28, trapElectrodeNumber=1),
        '02': channelConfiguration(27, trapElectrodeNumber=2),
        '03': channelConfiguration(24, trapElectrodeNumber=3),
        '04': channelConfiguration(5, trapElectrodeNumber=4),
        '05': channelConfiguration(14, trapElectrodeNumber=5),
        '06': channelConfiguration(18, trapElectrodeNumber=6),
        '07': channelConfiguration(16, trapElectrodeNumber=7),
        '08': channelConfiguration(13, trapElectrodeNumber=8),
        '09': channelConfiguration(11, trapElectrodeNumber=9),
        '10': channelConfiguration(9, trapElectrodeNumber=10), # broken, ground outside
        '11': channelConfiguration(10, trapElectrodeNumber=11), # broken, ground outside
        '12': channelConfiguration(7, trapElectrodeNumber=12),
        '13': channelConfiguration(8, trapElectrodeNumber=13),
        '14': channelConfiguration(26, trapElectrodeNumber=14),
        '15': channelConfiguration(25, trapElectrodeNumber=15),
        '16': channelConfiguration(23, trapElectrodeNumber=16),
        '17': channelConfiguration(4, trapElectrodeNumber=17),
        '18': channelConfiguration(19, trapElectrodeNumber=18),
        '19': channelConfiguration(17, trapElectrodeNumber=19),
        '20': channelConfiguration(3, trapElectrodeNumber=20),
        '21': channelConfiguration(20, trapElectrodeNumber=21),
        '22': channelConfiguration(12, trapElectrodeNumber=22),
        '23': channelConfiguration(6, trapElectrodeNumber=23) #6
        }

    smaDict = {
        'RF bias': channelConfiguration(1, smaOutNumber=1, name='RF bias', boardVoltageRange=(-40., 40.), allowedVoltageRange=(-2.0, 0))
        }
