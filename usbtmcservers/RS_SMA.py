'''
### BEGIN NODE INFO
[info]
name = RS_SMA server
version = 1.0
description =
instancename = RS_SMA server
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

from datetime import datetime as dt
import usb
import usbtmc
import numpy as np
from datetime import timedelta as td
from math import pi

SERVERNAME = 'RS_SMA server'
SIGNALID = 190233

class RS_SMAServer(LabradServer):
    name = 'RS_SMA'
    instr = None

    def initServer(self):
        self.frequency = yield self.getFrequency()
        self.amplitude = yield self.getAmplitude()
        self.output = yield self.getOutput()
        self.phase = None    	
        pass

    @inlineCallbacks
    def getFrequency(self):
        frequency = float(self.ask(self.instr, "SOURce:FREQuency?"))
        self.frequency = frequency / 10.**6 #now in MHz
        returnValue(self.frequency)

    @inlineCallbacks
    def getAmplitude(self):
        self.amplitude = float(self.ask(self.instr, "POWer?"))
        returnValue(self.amplitude)
    
    @inlineCallbacks
    def getOutput(self):
        state = float(self.ask(self.instr, "OUTput:STATe?"))
        self.state = bool(state)
        returnValue(self.state)

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

    @setting(5, 'Frequency', f=['v[MHz]'], returns=['v[MHz]'])
    def frequency(self, c, f=None):
        """Get or set the CW frequency."""
        if f is not None:
            self.frequency = float(self.write(self.instr, 'SOURce:FREQuency {}MHZ'.format(float(f))))
            self.frequency = f / 10.**6 #now in MHz
        returnValue(frequency)    

    @setting(6, 'Amplitude', a=['v[dBm]'], returns=['v[dBm]'])
    def amplitude(self, c, a=None):
        """Get or set the CW amplitude."""
        if a is not None:
            float(self.write(self.instr, 'POWer {}'.format(float(a)))
            self.amplitude = a
        returnValue(amplitude)

    @setting(7, 'Output', os=['b'], returns=['b'])
    def output_state(self, c, os=None):
        """Get or set the output status."""
        if os is not None:
        	bool(self.write(self.instr, 'OUTput:STATe {}'.format(int(out))))
            self.output= os
        returnValue(output)



__server__ = RS_SMAServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)   