import ok
from hardwareConfiguration import hardwareConfiguration

class api(object):
    '''class containing all commands for interfacing with the fpga'''
    def __init__(self):
        self.xem = None
        self.okDeviceID = hardwareConfiguration.okDeviceID
        self.okDeviceFile = hardwareConfiguration.okDeviceFile
        self.haveSecondPMT = hardwareConfiguration.secondPMT
        self.haveDAC = hardwareConfiguration.DAC
        
    def checkConnection(self):
        if self.xem is None: raise Exception("FPGA not connected")
    
    def connectOKBoard(self):
        fp = ok.FrontPanel()
        module_count = fp.GetDeviceCount()
        print "Found {} unused modules".format(module_count)
        for i in range(module_count):
            serial = fp.GetDeviceListSerial(i)
            tmp = ok.FrontPanel()
            tmp.OpenBySerial(serial)
            iden = tmp.GetDeviceID()
            if iden == self.okDeviceID:
                self.xem = tmp
                print 'Connected to {}'.format(iden)
                self.programOKBoard()
                return True
        return False
    
    def programOKBoard(self):
        prog = self.xem.ConfigureFPGA(self.okDeviceFile)
        if prog: raise Exception ("Not able to program FPGA")
        # this configure the PLL for the XEM6010. Probably need to change for other OK module
        pll = ok.PLL22150()
        self.xem.GetEepromPLL22150Configuration(pll)
        pll.SetDiv1(pll.DivSrc_VCO,4)
        self.xem.SetPLL22150Configuration(pll)
        
    def programBoard(self, sequence):
        sequence_data = self.padTo16(sequence)
        self.xem.WriteToBlockPipeIn(0x80, 16, sequence_data)
  
    def startLooped(self):
        '''
        Start the pulse sequence and make it loops forever
        '''
        self.xem.SetWireInValue(0x00,0x06,0x06)
        self.xem.UpdateWireIns()
    
    def stopLooped(self):
        '''
        Stop the pulse sequence (but will loop forever again if started
        '''
        self.xem.SetWireInValue(0x00,0x02,0x06)
        self.xem.UpdateWireIns()
        
    def startSingle(self):
        '''
        Start a single iteration of the pulse sequence
        '''
        self.xem.SetWireInValue(0x00,0x04,0x06)
        self.xem.UpdateWireIns()
    
    def stopSingle(self):
        '''
        Stop the single iteration of the pulse sequence
        '''
        self.xem.SetWireInValue(0x00,0x00,0x06)
        self.xem.UpdateWireIns()
    
    def setNumberRepeatitions(self, number):
        '''
        For a finte number of iteration, set the number of iteration
        '''
        self.xem.SetWireInValue(0x05, number)
        self.xem.UpdateWireIns()
    
    def resetRam(self):
        '''
        Reset the ram position of the pulser. Important to do this before writing the new sequence.
        '''
        self.xem.ActivateTriggerIn(0x40,1)
        
    def resetSeqCounter(self):
        '''
        Reset the counter to see how many iterations have been executed.
        '''
        self.xem.ActivateTriggerIn(0x40,0)
    
    def resetFIFONormal(self):
        '''
        Reset the FIFO on the FPGA for the normal PMT counting
        '''
        self.xem.ActivateTriggerIn(0x40,2)
    
    def resetFIFOResolved(self):
        '''
        Reset the FIFO on the FPGA for the time-tagged photon counting
        '''
        self.xem.ActivateTriggerIn(0x40,3)
        
    def resetFIFOReadout(self):
        '''
        Reset the FIFO on the FPGA for the read-out count.
        '''
        self.xem.ActivateTriggerIn(0x40,4)
 
    def setModeNormal(self):
        """user selects PMT counting rate"""
        self.xem.SetWireInValue(0x00,0x00,0x01)
        self.xem.UpdateWireIns()
    
    def setModeDifferential(self):
        """pulse sequence controls the PMT counting rate"""
        self.xem.SetWireInValue(0x00,0x01,0x01)
        self.xem.UpdateWireIns()
    
    def isSeqDone(self):
        '''
        check if the pulse sequece is done executing or not
        '''
        self.xem.SetWireInValue(0x00,0x00,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
    
    def getResolvedTotal(self):
        '''
        Get the number of photons counted in the FIFO for the time-resolved photon counter.
        '''
        self.xem.UpdateWireOuts()
        counted = self.xem.GetWireOutValue(0x22)
        return counted
    
    def getResolvedCounts(self, number):
        '''
        Get the time-tagged photon data.
        '''
        #buf = "\x00"*(number*2)
        buf = bytearray(number*2)
        self.xem.ReadFromBlockPipeOut(0xa0,2,buf)
        buf = str(buf)
        return buf
    
    def getNormalTotal(self):
        '''
        Get the number of normal PMT counts. (How many data in the FIFO)
        '''
        self.xem.SetWireInValue(0x00,0x40,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
    
    def getNormalCounts(self, number):
        '''
        Get the normal PMT counts from the FIFO.
        '''
        #buf = "\x00"* ( number * 2 )
        buf = bytearray(number * 2)
        self.xem.ReadFromBlockPipeOut(0xa1,2,buf)
        buf = str(buf)
        return buf
    
    def getReadoutTotal(self):
        '''
        Get the number of readout count.
        '''
        self.xem.SetWireInValue(0x00,0x80,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
        
    def getReadoutCounts(self, number):
        '''
        Get the readout count data.
        '''
        #buf = "\x00"* ( number * 2 )
        buf = bytearray(number*2)
        self.xem.ReadFromBlockPipeOut(0xa2,2,buf)
        buf = str(buf)
        return buf
    
    def howManySequencesDone(self):
        '''
        Get the number of iteratione executed.
        '''
        self.xem.SetWireInValue(0x00,0x20,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        completed = self.xem.GetWireOutValue(0x21)
        return completed
    
    def setPMTCountRate(self, time):
        #takes time in seconds
        self.xem.SetWireInValue(0x01,int(1000 * time))
        self.xem.UpdateWireIns()
        
    def setAuto(self, channel, inversion):
        '''
        Set the logic of the TTL to be auto or not
        '''
        self.xem.SetWireInValue(0x02,0x00, 2**channel)
        if not inversion:
            self.xem.SetWireInValue(0x03,0x00, 2**channel)
        else:
            self.xem.SetWireInValue(0x03,2**channel, 2**channel)
        self.xem.UpdateWireIns()
    
    def setManual(self, channel, state):
        '''
        Set the logic of the TTL to be manual or not
        '''
        self.xem.SetWireInValue(0x02,2**channel, 2**channel )
        if state:
            self.xem.SetWireInValue(0x03,2**channel, 2**channel)
        else:
            self.xem.SetWireInValue(0x03,0x00, 2**channel)
        self.xem.UpdateWireIns()
        
    def resetAllDDS(self):
        '''Reset the ram position of all dds chips to 0'''
        self.xem.ActivateTriggerIn(0x40,4)
    
    def advanceAllDDS(self):
        '''Advance the ram position of all dds chips'''
        self.xem.ActivateTriggerIn(0x40,5)
    
    def setDDSchannel(self, chan):
        '''select the dds chip for communication'''
        self.xem.SetWireInValue(0x04,chan)
        self.xem.UpdateWireIns()
        
    def padTo16(self,data):
        '''
        Padding function to make the data a multiple of 16
        '''
        size_needed = (16 - len(data)%16)%16
        zero_padding = bytearray(size_needed)
        return data+zero_padding
    
    def programDDS(self, prog):
        '''program the dds channel with a list of frequencies and amplitudes. The channel of the particular channel must be selected first'''
        ### add the initial padding
        prog = bytearray.fromhex(u'0000') + prog
#         for i in range(len(prog)):
#             print "prog dds",i,"=", prog[i]
        ### pad to a multiple of 16 bytes
        prog_padded = self.padTo16(prog)
        self.xem.WriteToBlockPipeIn(0x81, 16, prog_padded)  # very important !!! second argument need to be 16. Don't change this.
        #print "program DDS"
    
    def initializeDDS(self):
        '''force reprogram of all dds chips during initialization'''
        self.xem.ActivateTriggerIn(0x40,6)
    
    #Methods relating to line triggering
    def enableLineTrigger(self, delay = 0):
        '''sets delay value in microseconds'''
        min_delay, max_delay = hardwareConfiguration.lineTriggerLimits 
        if not min_delay <= delay <= max_delay: raise Exception("Incorrect Delay Time for Line Triggering")
        self.xem.SetWireInValue(0x06,delay)
        self.xem.SetWireInValue(0x00,0x08,0x08)
        self.xem.UpdateWireIns()    
        
    def disableLineTrigger(self):
        self.xem.SetWireInValue(0x00,0x00,0x08)
        self.xem.UpdateWireIns()     
        
# secondary PMT is not implemented anywhere. So no need for these two methods    
#     #Methods relating to using the optional second PMT
#     def getSecondaryNormalTotal(self):
#         if not self.haveSecondPMT: raise Exception ("No Second PMT")
#         self.xem.SetWireInValue(0x00,0xa0,0xf0)
#         self.xem.UpdateWireIns()
#         self.xem.UpdateWireOuts()
#         done = self.xem.GetWireOutValue(0x21)
#         return done
    
#     def getSecondaryNormalCounts(self, number):
#         if not self.haveSecondPMT: raise Exception ("No Second PMT")
#         buf = "\x00"* ( number * 2 )
#         self.xem.ReadFromBlockPipeOut(0xa3,2,buf)
#         return buf