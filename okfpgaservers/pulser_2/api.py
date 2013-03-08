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
        if prog: raise("Not able to program FPGA")
        pll = ok.PLL22393()
        self.xem.GetPLL22393Configuration(pll) ### load configuration
        pll.SetPLLParameters(0,25,3,True) ### PLL VCO setting: f = 48*25/3 = 400 MHz
        pll.SetOutputDivider(0,4) ### Output1: 400/4 = 100 MHz
        pll.SetOutputDivider(1,4) ### Output2: 400/4 = 100 MHz
        pll.SetOutputEnable(0, True) ### Enable output1
        pll.SetOutputEnable(1, True) ### Enable output2
        self.xem.SetPLL22393Configuration(pll) ### set PLL configuration
        self.resetSDRAM()
        
    def programBoard(self, sequence):
        self.xem.WriteToBlockPipeIn(0x80, 2, sequence)
  
    def startLooped(self):
        self.xem.SetWireInValue(0x00,0x06,0x06)
        self.xem.UpdateWireIns()
    
    def stopLooped(self):
        self.xem.SetWireInValue(0x00,0x02,0x06)
        self.xem.UpdateWireIns()
    
    def completeLooped(self):
        self.xem.SetWireInValue(0x00,0x04,0x06)
        self.xem.UpdateWireIns()
    
    def setNumberRepetitions(self, number):
        self.xem.SetWireInValue(0x05, number)
        self.xem.UpdateWireIns()
    
    def resetRam(self):
        self.xem.ActivateTriggerIn(0x40,1)
        
    def resetSeqCounter(self):
        self.xem.ActivateTriggerIn(0x40,0)
    
    def resetFIFONormal(self):
        self.xem.ActivateTriggerIn(0x40,2)
        
    def resetFIFOReadout(self):
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
        self.xem.SetWireInValue(0x00,0x00,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
    
    def getTimetagTotal(self):
        self.xem.UpdateWireOuts()
        number_of_photon = ((self.xem.GetWireOutValue(0x23)*65536 + self.xem.GetWireOutValue(0x22))+8)/4
        return number_of_photon
    
    def getTimetags(self, number):
        buf = "\x00"*(number*4)
        self.xem.ReadFromPipeOut(0xa0, buf)
        return buf
    
    def getNormalTotal(self):
        self.xem.SetWireInValue(0x00,0x40,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
    
    def getNormalCounts(self, number):
        buf = "\x00"* ( number * 2 )
        self.xem.ReadFromBlockPipeOut(0xa1,2,buf)
        return buf
    
    def getReadoutTotal(self):
        self.xem.SetWireInValue(0x00,0x80,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
        
    def getReadoutCounts(self, number):
        buf = "\x00"* ( number * 2 )
        self.xem.ReadFromBlockPipeOut(0xa2,2,buf)
        return buf
    
    def howManySequencesDone(self):
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
        self.xem.SetWireInValue(0x02,0x00, 2**channel)
        if not inversion:
            self.xem.SetWireInValue(0x03,0x00, 2**channel)
        else:
            self.xem.SetWireInValue(0x03,2**channel, 2**channel)
        self.xem.UpdateWireIns()
    
    def setManual(self, channel, state):
        self.xem.SetWireInValue(0x02,2**channel, 2**channel )
        if state:
            self.xem.SetWireInValue(0x03,2**channel, 2**channel)
        else:
            self.xem.SetWireInValue(0x03,0x00, 2**channel)
        self.xem.UpdateWireIns()
        
    def resetAllDDS(self):
        '''Reset the ram position of all dds chips to 0'''
        self.xem.ActivateTriggerIn(0x40,8)
    
    def advanceAllDDS(self):
        '''Advance the ram position of all dds chips'''
        self.xem.ActivateTriggerIn(0x40,5)
    
    def setDDSchannel(self, chan):
        '''select the dds chip for communication'''
        self.xem.SetWireInValue(0x04,chan)
        self.xem.UpdateWireIns()
    
    def programDDS(self, prog):
        '''program the dds channel with a list of frequencies and amplitudes. The channel of the particular channel must be selected first'''
        self.xem.WriteToBlockPipeIn(0x81, 2, prog)
    
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
        
    def resetSDRAM(self):
        '''
        resets the SDRAM that stores the timetags and enables write
        ''' 
        #reset SDRAM FIFO on fpga
        self.xem.SetWireInValue(0x07,0x0004)
        self.xem.UpdateWireIns()
        self.xem.SetWireInValue(0x07,0x0000)
        self.xem.UpdateWireIns()
        #enable write to memory
        self.xem.SetWireInValue(0x07,0x0002)
        self.xem.UpdateWireIns()
    
    def enableSDRAMread(self):
        '''
        enables the read mode on SDRAM
        '''
        self.xem.SetWireInValue(0x07,0x0000)
        self.xem.UpdateWireIns()
        self.xem.SetWireInValue(0x07,0x0004)
        self.xem.UpdateWireIns()
        self.xem.SetWireInValue(0x07,0x0000)
        self.xem.UpdateWireIns()
        self.xem.SetWireInValue(0x07,0x0001)
        self.xem.UpdateWireIns()
        
    #Methods relating to using the optional second PMT
    def getSecondaryNormalTotal(self):
        if not self.haveSecondPMT: raise Exception ("No Second PMT")
        self.xem.SetWireInValue(0x00,0xa0,0xf0)
        self.xem.UpdateWireIns()
        self.xem.UpdateWireOuts()
        done = self.xem.GetWireOutValue(0x21)
        return done
    
    def getSecondaryNormalCounts(self, number):
        if not self.haveSecondPMT: raise Exception ("No Second PMT")
        buf = "\x00"* ( number * 2 )
        self.xem.ReadFromBlockPipeOut(0xa3,2,buf)
        return buf
    
    #Methods relating to using optional DAC
    def resetFIFODAC(self):
        if not self.haveDAC: raise Exception ("No DAC")
        self.xem.ActivateTriggerIn(0x40,8)  
        
    def setDACVoltage(self, volstr):
        if not self.haveDAC: raise Exception ("No DAC")
        self.xem.WriteToBlockPipeIn(0x82, 2, volstr)   