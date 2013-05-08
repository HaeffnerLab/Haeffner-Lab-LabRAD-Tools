import ok
from DacConfiguration import hardwareConfiguration

class api(object):
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
        pll = ok.PLL22150()
        self.xem.GetEepromPLL22150Configuration(pll)
        pll.SetDiv1(pll.DivSrc_VCO,4)
        self.xem.SetPLL22150Configuration(pll)
        
    def programBoard(self, sequence):
        self.xem.WriteToBlockPipeIn(0x80, 2, sequence)
    
    def resetFIFODAC(self):
        self.xem.ActivateTriggerIn(0x40,8)  
        
    def setDACVoltage(self, volstr):
        self.xem.WriteToBlockPipeIn(0x82, 2, volstr)   
