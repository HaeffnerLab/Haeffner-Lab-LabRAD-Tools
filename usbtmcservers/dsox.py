'''
### BEGIN NODE INFO
[info]
name = DSOX server
version = 1.0
description =
instancename = DSOX server
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''

from labrad.server import LabradServer, setting, Signal, inlineCallbacks
from twisted.internet.defer import returnValue

from bokeh.plotting import figure, output_file, show, output_notebook
from bokeh.models import DatetimeTickFormatter

from datetime import datetime as dt
import usb
import usbtmc
import numpy as np
from datetime import timedelta as td
from math import pi

SERVERNAME = 'DSOX serverbbbb'
SIGNALID = 190233

class DsoxServer(LabradServer):
    name = 'DSOX3034A'
    instr = None

    def initServer(self):
        pass

    def ask(self, instr, q):
        try:
            answer = instr.ask(q)
            return str(answer)
        except AttributeError as ex:
            return 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            return 'Instrument is not connected... ' + str(ex)    

    def write(self, instr, q):
        try:
            answer = instr.write(q)
            return str(answer)
        except AttributeError as ex:
            return 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            return 'Instrument is not connected... ' + str(ex)    

    def read(self, instr, q):
        try:
            answer = instr.read(q)
            return str(answer)
        except AttributeError as ex:
            return 'Instrument is not connected... ' + str(ex)
        except ValueError as ex:
            return 'Instrument is not connected... ' + str(ex)    

    @setting(0, 'Connect', idProduct=['i'], idVendor=['i'], iSerialNumber=['s'], returns='s')
    def connect(self, c, idProduct, idVendor, iSerialNumber):
        '''Attempts to connect to usbtmc with idProduct, idVendor, iSerialNumber.'''
        #idProduct=0x0957
        #idVendor=0x17a4
        #iSerialNumber='MY51361370'
        try:
            if iSerialNumber != '':
                self.instr = usbtmc.Instrument(idProduct, idVendor, iSerialNumber)
            else:
                self.instr = usbtmc.Instrument(idProduct, idVendor)
            return "Succesfully connected."
        except Exception as inst:
            return str(inst)

    @setting(1, 'disconnect', returns='s')
    def disconnect(self, c):
        '''Disconnects from usbtmc.'''
        try:
            del self.instr
            return ''
        except AttributeError:        
            return 'No device to disconnect.'

    @setting(2, 'Identify', returns='s')
    def identify(self, c):
        '''Asks device to identify itself.'''
        return self.ask(self.instr, '*IDN?')

    @setting(3, 'clear status', returns='')
    def clearStatus(self, c):
        ''' 
        Clear status data structures, the device-defined error queue, and the Request-for-OPC flag.
        '''
        self.write(self.instr, "*CLS")

    @setting(4, 'reset', returns='')
    def reset(self, c):
        ''' 
        Returns instrument to its factory default settings
        '''
        self.write(self.instr, "*RST")

    @setting(5, 'auto scale', returns='')
    def autoScale(self, c):
        '''
        Autoscales scope display. 
        '''
        self.write(self.instr, ":AUToscale")

    @setting(6, 'acquire points', returns='i')
    def acquirePoints(self, c):
        '''
        Returns the number of data points that the hardware will acquire from the 
        input signal.
        '''
        return int(self.ask(self.instr, ":ACQuire:POINts?"))

    @setting(7, 'acquire srate', returns='i')
    def acquireSRate(self, c):
        '''
        Returns the current oscilloscope acquisition sample rate. The sample rate 
        is not directly controllable
        '''
        return int(self.ask(self.instr, ":ACQuire:SRATe?"))

    @setting(8, 'set acquire type', type = 's', returns='s')
    def setAcquireType(self, c, type):
        '''
        Selects the type of data acquisition that is to take place. The acquisition types are:
        normal, average, highres and peak.
        '''
        if type.lower() == 'normal':
            self.write(self.instr, ":ACQuire:TYPE NORMal")
            return ''
        elif type.lower() == 'average':
            self.write(self.instr, ":ACQuire:TYPE AVERage")
            return ''
        elif type.lower() == 'hres':
            self.write(self.instr, ":ACQuire:TYPE HRESolution")
            return ''
        elif type.lower() == 'peak':
            self.write(self.instr, ":ACQuire:TYPE PEAK")
            return ''
        else:
            return 'Invalid type.'

    @setting(9, 'acquire type', returns='s')
    def acquireType(self, c):
        '''Queries the setting for data acquisition type.'''
        return self.ask(self.instr, ":ACQuire:TYPE?")

    @setting(10, 'set waveform points', n='i', returns='')
    def setWaveformPoints(self, c, n):
        '''Sets the number of points actually transferred after acquisition.'''            
        self.write(self.instr, "WAVeform:POINts " + str(n))
    
    @setting(11, 'get waveform points', returns='i')
    def getWaveformPoints(self, c):
        '''Returns the number of points actually transferred after acquisition.'''
        return int(self.ask(self.instr, "WAVeform:POINts?"))

    @setting(12, 'set waveform format', type='s', returns='s')
    def setWaveformFormat(self, c, type):
        '''
        Sets the data transmission mode for waveform data points. This command 
        controls how the data is formatted when sent from the oscilloscope. 
        Options are ASCii, ASCII, WORD and BYTE.
        '''
        if type == 'ASCii':
            self.write(self.instr, "WAVeform:FORMat ASCii")
            return ''
        elif type == 'ASCII':
            elf.write(self.instr, "WAVeform:FORMat ASCI")
            return ''
        elif type == 'WORD':
            elf.write(self.instr, "WAVeform:FORMat WORD")
            return ''
        elif type == 'BYTE':
            elf.write(self.instr, "WAVeform:FORMat BYTE")
            return ''
        else:
            return 'Invalid type.'

    @setting(13, 'get waveform format', returns='s')
    def getWaveformFormat(self, c):
        '''Returns the data transmission mode for waveform data points.'''
        return self.ask(self.instr, "WAVeform:FORMat?")

    @setting(14, 'set waveform source', n='i', returns='s')
    def setWaveformSource(self, c, n):
        '''
        Takes as arg, the analog channel to be used as the source for the waveform commands.
        '''
        if n in range(1,5):
            self.write(self.instr, "WAVeform:SOURce CHANnel" + str(n))
            return ''
        else:
            return 'Channel out of range.'

    @setting(15, 'get waveform source', returns='s')
    def getWaveformSource(self, c):
        '''
        Returns the analog channel being used as the source for waveform commands.
        '''
        return self.ask(self.instr, "WAVeform:SOURce?")

    @setting(16, 'digitize', channel ='i', returns='s')
    def digitize(self, c, channel):
        '''
        A specialized RUN command. It causes the instrument to acquire waveforms 
        from channel <arg> according to the settings of the :ACQuire commands subsystem. 
        An arg of 0 results in all running channels to be digitized. 
        '''
        if channel == 0:
            self.write(self.instr, "DIGitize; :RUN")
            return ''
        elif channel in range(1,5):
            self.write(self.instr, "DIGitize CHANnel" + str(channel) + "; :RUN" )
            return ''
        else:
            return 'Channel out of range.'

    @setting(17, 'get waveform data', returns='*v[]')
    def getWaveformData(self, c):
        ''' Returns digitized waveform data as a list of floats.'''
        # raw_data = self.ask(self.instr, "WAVeform:DATA?")
        data = [float(i) for i in self.instr.ask("WAVeform:DATA?")[11:].split(",")]
        # try:
        #     data = [float(i) for i in self.instr.ask("WAVeform:DATA?")[11:].split(",")]
        # except:
        #     # Need to figure out what to do here
        #     data = raw_data
        return data

    @setting(18, 'get waveform preamble', returns='*v[]')
    def getWaveformPreamble(self, c):
        '''
        Returns a list of information about the most recently collected waveform data.
        Of the format: [x_increment, x_origin, x_ref, y_increment, y_origin, y_ref].
        '''
        preamble = self.ask(self.instr, "WAVeform:PREamble?")
        return list(preamble.split(","))[4:]

    @setting(19, 'set time scale', t = 'v[]', returns='s')
    def setTimeScale(self, c, t):
        '''
        Set the time/div for all channels. Takes as argument the time in seconds.
        '''
        if t>0:
            self.write(self.instr, "TIMebase:SCALe " + str(t))
            return ''       
        else:
            return "Can't input negative values."

    @setting(20, 'set scale', n='i', s='v', returns='s')
    def setScale(self, c, n, s):
        '''
        Sets the vertical scale/div. First argument is channel, second
        argument is volts/div. 
        '''
        if n in range(1,5) and s>0:
            self.write(self.instr, "CHANnel"+str(n)+":SCALe "+str(s)+"V")
            return ''
        else:
            return 'Invalid value for channel or volts/div.'

    @setting(21, 'get system date', returns='*i')
    def getSystemDate(self, c):
        '''
        Returns current system date in format (year, month, day).
        '''
        date = self.ask(self.instr, ":SYSTem:DATE?")
        return [int(i) for i in date.split(',')]

    @setting(22, 'get system time', returns='*i')
    def getSystemTime(self, c):
        '''
        Returns current device time in format (hours, minutes, seconds).
        '''
        t = self.ask(self.instr, "SYSTem:TIME?")
        return [int(i) for i in t.split(',')]

    @setting(23, 'set system date', ymd='(i,i,i)', returns='s')
    def setSystemDate(self, c, ymd):
        '''
        Sets device date according to year, month, day.
        '''
        if type(ymd[0])==int and type(ymd[1])==int and type(ymd[2])==int:
            self.write(self.instr, ":SYSTem:DATE %s, %s, %s" %(ymd[0],ymd[1],ymd[2]))
            return ''
        else:
            return 'Invalid date.'

    @setting(24, 'set system time', hms='(i,i,i)', returns='s')
    def setSystemTime(self, c, hms):
        '''
        Sets device time according to year, month, day.
        '''
        if type(hms[0])==int and type(hms[1])==int and type(hms[2])==int:
            self.write(self.instr, ":SYSTem:TIME %s, %s, %s" %(hms[0],hms[1],hms[2]))
            return ''
        else:
            return 'Invalid time.' 

    @setting(25, 'set time range', t='v[]', returns='')
    def setTimeRange(self, c, t):
        '''Sets time range in seconds.'''
        self.write(self.instr, ":TIMebase:RANGe " + str(t))

    @setting(26, 'set trigger source', channel = 'i', returns='')
    def setTriggerSource(self, c, channel):
        '''Sets channel that scope triggers on.'''
        self.write(self.instr, ":TRIGger:SOURce CHANnel" + str(channel))

    @setting(27, 'set trigger level', level='v[]', returns='')
    def setTriggerLevel(self, c, level):
        '''Sets the trigger level in volts.'''
        self.write(self.instr, ":TRIGger:LEVel " + str(level))

    @setting(28, 'set trigger reference left', returns='')
    def setTriggerReferenceLeft(self, c):
        '''
        Sets the trigger reference to the left. Scope will display waveform one time div
        after trigger to the left.
        '''
        self.write(self.instr, ":TIMebase:REFerence LEFT")

    @setting(29, 'display clear', returns='')
    def displayClear(self, c):
        '''Clears scope display.'''
        self.write(self.instr, ":DISPlay:CLEar")

__server__ = DsoxServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)                                                                                                                                      
