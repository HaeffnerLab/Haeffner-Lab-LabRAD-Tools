# Configuration file for the dac

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
            self.name = str(trapElectrodeNumber)
            if trapElectrodeNumber < 10: self.name +=' '
        else:
            self.name = name

class hardwareConfiguration(object):
    numElectrodes = 23
    numSmaOuts = 5
    numDacChannels = 28
    PREC_BITS = 16
    multipoles = ['Ex1', 'Ey1', 'Ez1', 'U2']
    pulseTriggered = False # Set to True to have the DAC voltages advance by a pulse trigger, else update as each value is written
    maxCache = 126 # Max number of voltages which can be cached to the DAC
    
    elecDict = {        
        '1 ': channelConfiguration(28, trapElectrodeNumber = 1),
        '2 ': channelConfiguration(27, trapElectrodeNumber = 2),
        '3 ': channelConfiguration(24, trapElectrodeNumber = 3),
        '4 ': channelConfiguration(5, trapElectrodeNumber = 4),
        '5 ': channelConfiguration(14, trapElectrodeNumber = 5),
        '6 ': channelConfiguration(18, trapElectrodeNumber = 6),
        '7 ': channelConfiguration(16, trapElectrodeNumber = 7),
        '8 ': channelConfiguration(13, trapElectrodeNumber = 8),
        '9 ': channelConfiguration(11, trapElectrodeNumber = 9),
        '10': channelConfiguration(1, trapElectrodeNumber = 10),
        '11': channelConfiguration(6, trapElectrodeNumber = 11),
        '12': channelConfiguration(7, trapElectrodeNumber = 12),
        '13': channelConfiguration(8, trapElectrodeNumber = 13),
        '14': channelConfiguration(26, trapElectrodeNumber = 14),
        '15': channelConfiguration(25, trapElectrodeNumber = 15),
        '16': channelConfiguration(23, trapElectrodeNumber = 16),        
        '17': channelConfiguration(4, trapElectrodeNumber = 17),        
        '18': channelConfiguration(19, trapElectrodeNumber = 18),
        '19': channelConfiguration(17, trapElectrodeNumber = 19),
        '20': channelConfiguration(3, trapElectrodeNumber = 20),
        '21': channelConfiguration(20, trapElectrodeNumber = 21),
        '22': channelConfiguration(12, trapElectrodeNumber = 22),
        '23': channelConfiguration(10, trapElectrodeNumber = 23),
        }

    smaDict = {
        'RF bias': channelConfiguration(9, smaOutNumber = 1, name = 'RF bias', boardVoltageRange = (-10., 10.), allowedVoltageRange = (-2.0, 0)),
        }