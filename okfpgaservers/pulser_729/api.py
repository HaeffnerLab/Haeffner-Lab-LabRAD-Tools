import ok
from hardwareConfiguration import hardwareConfiguration

class api():
    '''class containing all commands for interfacing with the fpga'''
    def __init__(self):
        self.xem = None
        self.okDeviceID = hardwareConfiguration.okDeviceID
        self.okDeviceFile = hardwareConfiguration.okDeviceFile
        
    def checkConnection(self):
        if self.xem is None: raise Exception("FPGA not connected")
    
    def connectOKBoard(self):
        fp = ok.FrontPanel()
        module_count = fp.GetDeviceCount()
        print "Found {} unused modules".format(module_count)
        for i in range(module_count):
            serial = fp.GetDeviceListSerial(i)
            fp.OpenBySerial(serial)
            device_id = fp.GetDeviceID()
            if device_id == self.okDeviceID:
                self.xem = fp
                print 'Connected to {}'.format(device_id)
                self.programOKBoard()
                return True
        return False
    
    def programOKBoard(self):
        prog = self.xem.ConfigureFPGA(self.okDeviceFile)
        if prog: raise("Not able to program FPGA")
        pll = ok.PLL22150()
        self.xem.GetEepromPLL22150Configuration(pll)
        pll.SetDiv1(pll.DivSrc_VCO,4)
        self.xem.SetPLL22150Configuration(pll)
       
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
    
    def programDDS(self, prog):
        '''program the dds channel with a list of frequencies and amplitudes. The channel of the particular channel must be selected first'''
        self.xem.WriteToBlockPipeIn(0x81, 2, prog)

    def initializeDDS(self):
        '''force reprogram of all dds chips during initialization'''
        self.xem.ActivateTriggerIn(0x40,6)
        
    def setControl(self, addr):
        self.xem.SetWireInValue(0x00,addr)
        self.xem.UpdateWireIns()