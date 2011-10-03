'''
Created on Jan 26, 2011
Last Modified July 25, 2011
@author: Christopher Reilly, Michael Ramm
'''
from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from twisted.internet import reactor
from twisted.internet.defer import returnValue
import binascii
from labrad.server import Signal

SERVERNAME = 'LaserDAC'
PREC_BITS = 16.
DAC_MAX = 2500.
MAX_QUEUE_SIZE = 1000
#time to wait for response from dc box
TIMEOUT = 1.0
#expected response from dc box after write
RESP_STRING = 'r'
#time to wait if correct response not received
ERROR_TIME = 1.0
SIGNALID = 270579

class DCBoxError( SerialConnectionError ):
    errorDict = {
        0:'Invalid channel name',
        1:'Voltage out of range',
        2:'Queue size exceeded',
        3:'Shutter input must be boolean',
        4:'Must set value before you can retrieve',
        5:'Correct response from DC box not received, sleeping for short period'
        }

class Channel():
    "Used to store information about channels"    
    def __init__(self, chanNumber, chanName, wavelength, range):
        self.chanNumber = chanNumber
        self.chanName = chanName
        self.chanWL = wavelength
        self.range = range
        self.voltage = None
        
class laserDACServer( SerialDeviceServer ):
    """
    LaserDAC Server
    Serial device controlling cavities and laser piezos
    """
    name = SERVERNAME
    regKey = 'LaserRoomDac'
    port = None
    serNode = 'lab-49'
    timeout = TIMEOUT
    onNewUpdate = Signal(SIGNALID, 'signal: channel has been updated', '(sv)')
       

    @inlineCallbacks
    def initServer( self ):
        """
        Initialize laserDACServer
        """
        self.createInfo()
        self.queue = []
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        try:
            print self.serNode
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
        self.populateInfo()
        self.listeners = set()
        self.free = True

    def createInfo( self ):
        """
        Initializes the list of Channels
        """
        self.channelList = []
        self.channelList.append(Channel(0,'397',397,(0.0,2500.0)))
        self.channelList.append(Channel(1,'866',866,(0.0,2500.0)))
        self.channelList.append(Channel(2,'422',422,(0.0,2500.0)))
        self.channelList.append(Channel(3,'397S',397,(0.0,2500.0)))
        self.channelList.append(Channel(4,'732',732,(0.0,2500.0)))
 
    @inlineCallbacks
    def populateInfo(self):
        
        """
        Gets the information about the current channels from the hardware
        """
        for givenChannel in self.channelList:
            chanNum = givenChannel.chanNumber
            voltage = yield self.acquireVoltage(chanNum)
            givenChannel.voltage = voltage
    
    @inlineCallbacks
    def acquireVoltage(self, chan):
        comstring = str(chan)+'r'
        yield self.ser.write(comstring)
        encoded = yield self.ser.read(3)
        seq = int(binascii.hexlify(encoded[0:2]),16)
        voltage = int(round(float(seq * DAC_MAX) / (2**16 - 1)))
        returnValue(voltage)
            
    @inlineCallbacks
    def checkQueue( self ):
        """
        When timer expires, check queue for values to write
        """
        if self.queue:
            print 'clearing queue...(%d items)' % len( self.queue )
            yield self.writeToSerial( *self.queue.pop( 0 ) )
        else:
            print 'queue free for writing'
            self.free = True

    def tryToSend( self, givenChannel, value ):
        """
        Check if serial connection is free.
        If free, write value to channel.
        If not, store channel and value as tuple in queue.
        Raise error when queue fills up.
        
        @param channel: Channel to write to
        @param value: Value to write
        
        @raise DCBoxError: Error code 2.  Queue size exceeded
        """
        if self.free:
            self.free = False
            self.writeToSerial( givenChannel, value )
        elif len( self.queue ) > MAX_QUEUE_SIZE:
            raise DCBoxError( 2 )
        else: self.queue.append( ( givenChannel, value ) )

    @inlineCallbacks
    def writeToSerial( self, givenChannel, value ):
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
        toSend = self.mapMessage( givenChannel, value )
        print toSend
        self.ser.write( toSend )
        resp = yield self.ser.read( len( RESP_STRING ) )
        if RESP_STRING != resp:
#            Since we didn't get the the correct response,
#            place the value back in the front of the queue
#            and wait for a specified ERROR_TIME before
#            checking the queue again.
            self.queue.insert( 0, ( givenChannel, value ) )
            reactor.callLater( ERROR_TIME, self.checkQueue )
            raise DCBoxError(5)
        else:
#            Since we got the correct response,
#            update the value entry for this channel
#            and check the queue.
            givenChannel.voltage = value
            self.checkQueue()

    def getChannel( self, chanName ):
        """
        Find the channel class corresponding to the given channel name
        """
        for givenChannel in self.channelList:
            if givenChannel.chanName == chanName:
                return givenChannel
        raise DCBoxError( 0 )

    def validateInput( self, givenChannel, voltage ):
        """
        Check to see if value lies within specified channel's range.        
        """
        MIN, MAX = givenChannel.range
        if not MIN <= voltage <= MAX: raise DCBoxError( 1 )

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
    def notifyOtherListeners(self, context, chanInfo):
        """
        Notifies all listeners except the one in the given context
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        self.onNewUpdate(chanInfo, notified)
    
    @setting( 0 , chanName = 's: which laser (i.e 397 )',voltage = 'v: voltage to apply',returns = '' )
    def setVoltage( self, c, chanName, voltage ):
        """
        Sets the DAC Voltage on the channel with name chanName
        """
        givenChannel = self.getChannel(chanName )
        self.validateInput( givenChannel, voltage )
        self.tryToSend( givenChannel, voltage )
        self.notifyOtherListeners(c, (chanName,voltage))

    @setting( 1 , chanName = 's: which laser (i.e 397 )',returns = 'v: voltage' )
    def getVoltage( self, c, chanName ):
        """
        Retrieve the DAC voltage on the channel with name chanName
        """
        givenChannel = self.getChannel(chanName )
        voltage = givenChannel.voltage
        if voltage is not None: return voltage
        else: raise DCBoxError( 4 )
    
    @setting(2, returns = '*s')
    def getChannelNames(self, c):
        """
        Returns the list of available channel names
        """
        names = []
        for givenChannel in self.channelList:
            names.append(givenChannel.chanName)
        return names

    #DAC is 16 bit, so the function accepts voltage in mv and converts it to a sequential representation                                                                               
    #2500 -> 2^16 , #1250 -> 2^15
    @staticmethod
    def voltageToFormat( voltage ):
        return int( ( 2. ** PREC_BITS - 1 ) * voltage / DAC_MAX )

    #converts sequential representation to string understood by microcontroller                                                                                                        
    #i.e ch 1 set 2500mv -> '1,str' where str =  is  character representation of 0xffff given by binascii.unhexlify(ffff)
    @staticmethod
    def makeComString( channel, binVolt ):
        hexrepr = hex( binVolt )[2:] #select ffff out of 0xfff'                                                                                                                          
        hexrepr = hexrepr.zfill( 4 ) #left pads to make sure 4 characters                                                                                                            
        numstr = binascii.unhexlify( hexrepr ) #converts ffff to ascii characters                                                                                                    
        comstring = str( channel ) + ',' + numstr
        return comstring

    def mapMessage( self, givenChannel, value ):
        """
        Map value to serial string for specified channel.
        
        Note that channel is different from device channel.
        
        @param channel: Use channel to determine mapping parameters
        @param value: Value to be converted
        
        @return: value formatted for serial communication
        """
        def mapVoltage( value, range ):
            return ( float( value ) - float( range[0] ) ) * DAC_MAX / ( range[1] - range[0] )
        range = givenChannel.range
        chanNumber = givenChannel.chanNumber
        return self.makeComString( chanNumber, self.voltageToFormat( mapVoltage( value, range ) ) )
    
if __name__ == "__main__":
    from labrad import util
    util.runServer( laserDACServer() )


