class FPGA_Simu(object):
    '''class containing all commands for interfacing with the fpga'''
    def __init__(self):
        
        self.show_debug_messages = False 
        
        print "Initializing FPGA ..."
                
    def ConfigureFPGA(self, okDeviceFile):
        print "Configuring FPGA ..."

    def SetWireInValue(self, *arg):
        if self.show_debug_messages:
            print "Setting Wire In Value", arg

    def UpdateWireIns(self):
        if self.show_debug_messages:
            print "Updating Wire Ins ..."

    def UpdateWireOuts(self):
        if self.show_debug_messages:
            print "Updating Wire Outs ..."

    def GetWireOutValue(self, *arg):
        if self.show_debug_messages:
            print "Get Wire Out Value ...", arg
        # the return number must be 'divisible' by 2
        return 25

    def ActivateTriggerIn(self, a, b):
        if self.show_debug_messages:
            print "Activate Trigger In ...", a, b

    def WriteToBlockPipeIn(self, *arg):
        if self.show_debug_messages:
            print "Write to block pipe in ...", arg

    def ReadFromPipeOut(self, *arg):
        if self.show_debug_messages:
            print "Read from pipe out ...", arg

    def ReadFromBlockPipeOut(self, *arg):
        if self.show_debug_messages:
            print "Read from block pipe out ...", arg
        
