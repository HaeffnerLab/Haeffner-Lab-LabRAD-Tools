'''
Created on April 5, 2011

@author: michaelramm
'''

from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
import binascii

SERVERNAME = 'HighVoltA'
MINRANGE = 0.0
RANGE = 4000.0
PREC_BITS = 10
MAX_QUEUE_SIZE = 1000
#time to wait for response from dc box
TIMEOUT = 1.0
#expected response from dc box after write
RESP_STRING = 'r'
#time to wait if correct response not received
ERROR_TIME = 1.0



class HighVoltBoxError( SerialConnectionError ):
    errorDict = {
        0:'Invalid device channel',
        1:'Value out of range',
        2:'Queue size exceeded',
        3:'Shutter input must be boolean',
        4:'Must set value before you can retrieve',
        5:'Correct response from DC box not received, sleeping for short period'
        }

class HighVoltBoxA( SerialDeviceServer ):
    name = SERVERNAME
    regKey = 'HighVoltA'
    port = None
    serNode = 'lattice-pc'
    timeout = TIMEOUT

    @inlineCallbacks
    def initServer( self ):
        """
        Initialize DC Box server
        
        Initializes dictionary (dcDict) of relevant device data
        Initializes queue (queue) for commands to send
        Initializes serial connection
        Frees connection for writing
        
        @raise SerialDeviceError: (For subclass author) Define regKey and serNode attributes
        """
        self.createDict()
        self.queue = []
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        try:
            serStr = yield self.findSerial( self.serNode )
            self.initSerial( serStr, port )
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise
        self.populateDict()
        self.free = True
    
    def createDict(self):
        self.dict = {'voltage':None}
    
    @inlineCallbacks
    def populateDict(self):
        yield self.ser.write('r')
        reading = yield self.ser.read(5)
        form = int(reading[0:4])
        self.dict['voltage'] = self.formatToVoltage(form)
        print self.dict
        
    @inlineCallbacks
    def checkQueue( self ):
        """
        When timer expires, check queue for values to write
        """
        if self.queue:
            print 'clearing queue...(%d items)' % len( self.queue )
            yield self.writeToSerial( self.queue.pop( 0 ) )
        else:
            print 'queue free for writing'
            self.free = True

    def tryToSend( self, value ):
        """
        Check if serial connection is free.
        If free, write value to channel.
        If not, store channel and value as tuple in queue.
        Raise error when queue fills up.
        
        @param channel: Channel to write to
        @param value: Value to write
        
        @raise HighVoltBoxA: Error code 2.  Queue size exceeded
        """
        if self.free:
            self.free = False
            self.writeToSerial( value )
        elif len( self.queue ) > MAX_QUEUE_SIZE:
            raise HighVoltBoxA( 2 )
        else: self.queue.append( value )

    @inlineCallbacks
    def writeToSerial( self, value ):
        """
        Write value to specified channel through serial connection.
        
        Convert message to microcontroller's syntax.
        Check for correct response.
        Handle possible error, or
        save written value to memory and check queue.
        
        @param channel: Channel to write to
        @param value: Value to write
        
        @raise SerialConnectionError: Error code 2.  No open serial connection.
        """
        self.checkConnection()
        toSend = self.mapMessage( value )
        self.ser.write( toSend )
        resp = yield self.ser.read( len( RESP_STRING ) )
        if RESP_STRING != resp:
#            Since we didn't get the the correct response,
#            place the value back in the front of the queue
#            and wait for a specified ERROR_TIME before
#            checking the queue again.
            self.queue.insert( 0, value )
            reactor.callLater( ERROR_TIME, self.checkQueue )
            raise HighVoltBoxError(5)
        else:
            self.checkQueue()

    def validateInput( self, value ):
        """
        Check to see if value lies within specified device's range.
                
        @raise HighVoltBoxA: Error code 1.  Value not within device's range.
        """
        if not MINRANGE <= value <= RANGE: raise HighVoltBoxError( 1 )

    
    def mapMessage( self, value ):
        """
        Map value to serial string for specified channel.
               
        @return: value formatted for serial communication
        """
        return self.makeComString( self.voltageToFormat(  value  ) )
    
    
    @staticmethod
    def makeComString( num ):
        """
        takes a a number of converts it to a string understood by microcontroller, i.e 23 -> C0023!
        """
        comstring = 'C' + str( num ).zfill( 4 ) + '!'
        return comstring
    
    @staticmethod
    def voltageToFormat( volt ):
        return int(round( ( volt / RANGE ) * (2.**PREC_BITS-1) ) ) 
    
    @staticmethod
    def formatToVoltage( form ):
        return int(round(form * RANGE / (2.**PREC_BITS-1)))

    
    @setting( 0 , voltage = 'v: voltage to apply', returns = '' )
    def setVoltage( self, c, voltage ):
        """
        Sets the voltage.
        """
        self.validateInput( voltage )
        self.tryToSend( voltage )
        self.dict['voltage'] = voltage

    @setting( 1 , returns = 'v: voltage' )
    def getVoltage( self, c ):
        """
        Retrieve current voltage
        """
        value = self.dict['voltage']
        if value is not None: return value
        else: raise HighVoltBoxA( 4 )

if __name__ == "__main__":
    from labrad import util
    util.runServer( HighVoltBoxA() )


