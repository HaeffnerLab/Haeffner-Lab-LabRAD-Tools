from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue
from twisted.internet.threads import deferToThread
from ctypes import c_long, c_buffer, c_float, windll, pointer
from APT_config import stageConfiguration

"""
### BEGIN NODE INFO
[info]
name =  APT Motor Server
version = 1.1
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

class APTMotor():
    def __init__(self):
        self.aptdll = windll.LoadLibrary("APT.dll")
        #self.aptdll.EnableEventDlg(False)
        self.aptdll.APTInit()
        self.config=stageConfiguration()
        print 'APT initialized'
        self.HWType = c_long(31) # 31 means TDC001 controller
    
    def getNumberOfHardwareUnits(self):
        numUnits = c_long()
        self.aptdll.GetNumHWUnitsEx(self.HWType, pointer(numUnits))
        return numUnits.value
    
    def getSerialNumber(self, index):
        HWSerialNum = c_long()
        hardwareIndex = c_long(index)
        self.aptdll.GetHWSerialNumEx(self.HWType, hardwareIndex, pointer(HWSerialNum))
        return HWSerialNum.value

    def initializeHardwareDevice(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        self.aptdll.InitHWDevice(HWSerialNum)
        # need some kind of error reporting here
        return True

    def getHardwareInformation(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        model = c_buffer(255)
        softwareVersion = c_buffer(255)
        hardwareNotes = c_buffer(255)
        self.aptdll.GetHWInfo(HWSerialNum, model, 255, softwareVersion, 255, hardwareNotes, 255)      
        hwinfo = [model.value, softwareVersion.value, hardwareNotes.value]
        return hwinfo
    
    def getStageAxisInformation(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        minimumPosition = c_float()
        maximumPosition = c_float()
        units = c_long()
        pitch = c_float()
        self.aptdll.MOT_GetStageAxisInfo(HWSerialNum, pointer(minimumPosition), pointer(maximumPosition), pointer(units), pointer(pitch))
        stageAxisInformation = [minimumPosition.value, maximumPosition.value, units.value, pitch.value]
        return stageAxisInformation
    
    def setStageAxisInformation(self, serialNumber, minimumPosition, maximumPosition):
        HWSerialNum = c_long(serialNumber)
        minimumPosition = c_float(minimumPosition)
        maximumPosition = c_float(maximumPosition)
        units = c_long(1) #units of mm
        # Get different pitches of lead screw for moving stages for different lasers. 
        pitch = c_float(self.config.get_pitch(serialNumber)) 
        self.aptdll.MOT_SetStageAxisInfo(HWSerialNum, minimumPosition, maximumPosition, units, pitch)
        return True

    def getHardwareLimitSwitches(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        reverseLimitSwitch = c_long()
        forwardLimitSwitch = c_long()
        self.aptdll.MOT_GetHWLimSwitches(HWSerialNum, pointer(reverseLimitSwitch), pointer(forwardLimitSwitch))
        hardwareLimitSwitches = [reverseLimitSwitch.value, forwardLimitSwitch.value]
        return hardwareLimitSwitches
    
    def getVelocityParameters(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        minimumVelocity = c_float()
        acceleration = c_float()
        maximumVelocity = c_float()
        self.aptdll.MOT_GetVelParams(HWSerialNum, pointer(minimumVelocity), pointer(acceleration), pointer(maximumVelocity))
        velocityParameters = [minimumVelocity.value, acceleration.value, maximumVelocity.value]
        return velocityParameters
    
    def setVelocityParameters(self, serialNumber, minVel, acc, maxVel):
        HWSerialNum = c_long(serialNumber)
        minimumVelocity = c_float(minVel)
        acceleration = c_float(acc)
        maximumVelocity = c_float(maxVel)
        self.aptdll.MOT_SetVelParams(HWSerialNum, minimumVelocity, acceleration, maximumVelocity)
        return True
    
    def getVelocityParameterLimits(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        maximumAcceleration = c_float()
        maximumVelocity = c_float()
        self.aptdll.MOT_GetVelParamLimits(HWSerialNum, pointer(maximumAcceleration), pointer(maximumVelocity))
        velocityParameterLimits = [maximumAcceleration.value, maximumVelocity.value]
        return velocityParameterLimits  

    def getPosition(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        position = c_float()
        self.aptdll.MOT_GetPosition(HWSerialNum, pointer(position))
        return position.value    

    def moveRelative(self, serialNumber, relDistance):
        HWSerialNum = c_long(serialNumber)
        relativeDistance = c_float(relDistance)
        self.aptdll.MOT_MoveRelativeEx(HWSerialNum, relativeDistance, True)
        return True

    def moveAbsolute(self, serialNumber, absPosition):
        HWSerialNum = c_long(serialNumber)
        absolutePosition = c_float(absPosition)
        self.aptdll.MOT_MoveAbsoluteEx(HWSerialNum, absolutePosition, True)
        return True

    def identify(self, serialNumber):
        HWSerialNum = c_long(serialNumber)
        self.aptdll.MOT_Identify(HWSerialNum)
        return True
        
    def cleanUpAPT(self):
        self.aptdll.APTCleanUp()
        print 'APT cleaned up'  

class stage(object):
    """
    Convinience object for storing information about translation stages
    """
    def __init__(self, name, serial):
        self.name = name
        self.serial = serial
        self.initialized = False
        self.minpos = -6.5
        self.maxpos = 6.5

class APTMotorServer(LabradServer):
    """ Contains methods that interact with the APT motor controller """
    
    name = "APT Motor Server"
    
    onVelocityParameterChange = Signal(111111, 'signal: velocity parameter change', 'w')
    onPositionChange = Signal(222222, 'signal: position change', 'w')
    
    def initServer(self):
        user_config = stageConfiguration.devicenames
        self.deviceDict = {}
        for name,stage_serial in user_config:
            self.deviceDict[name] = stage(name,stage_serial) 
        self.listeners = set()  
        self.prepareDevices()
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
        
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    def prepareDevices(self):
        self.aptMotor = APTMotor()        
        numberOfHardwareUnits = self.aptMotor.getNumberOfHardwareUnits()
        connectedSerials = [self.aptMotor.getSerialNumber(i) for i in range(numberOfHardwareUnits)]
        print '{} units connected: {}'.format(numberOfHardwareUnits,connectedSerials)
        for stage in self.deviceDict.values():
            if stage.serial in connectedSerials:
                ok = self.aptMotor.initializeHardwareDevice(stage.serial)
                if ok: stage.initialized = True
                self.aptMotor.setStageAxisInformation(stage.serial, stage.minpos, stage.maxpos)
    
    def getInitialized(self):
        initialized = [stage.name for stage in self.deviceDict.values() if stage.initialized]
        return initialized 
               
    @setting(0, "Get Available Devices", returns = '*s')
    def getAvailableDevices(self, c):
        """Returns a List of Initialized Devices"""
        return self.getInitialized()

    @setting(1, "Select Device", name = 's', returns = '')
    def selectDevice(self, c, name):
        if name not in self.getInitialized(): raise Exception("No such Device")
        c['Device'] = self.deviceDict[name].serial

    @setting(2, "Get Serial Number", returns = 'w')
    def getSerialNumber(self, c):
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        return serial
    
    @setting(3, "Get Device Information",  returns ='*s')
    def getHardwareInformation(self, c):
        """Returns Hardware Information: Model, Software Version, Hardware Notes"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        info = yield deferToThread(self.aptMotor.getHardwareInformation, serial)
        returnValue(info)

    @setting(4, "Get Velocity Parameters", returns ='*v')
    def getVelocityParameters(self, c):
        """Returns Velocity Parameters: Minimum Velocity, Acceleration, Maximum Velocity"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        info = yield deferToThread(self.aptMotor.getVelocityParameters, serial)
        returnValue(info)

    @setting(5, "Get Velocity Parameter Limits", returns ='*v')
    def getVelocityParameterLimits(self, c):
        """Returns Velocity Parameter Limits: Maximum Acceleration, Maximum Velocity"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        info = yield deferToThread(self.aptMotor.getVelocityParameterLimits, serial)
        returnValue(info)

    @setting(6, "Set Velocity Parameters", minimumVelocity = 'v', acceleration = 'v', maximumVelocity = 'v', returns ='b')
    def setVelocityParameters(self, c, minimumVelocity, acceleration, maximumVelocity):
        """Sets Velocity Parameters
            Minimum Velocity, Acceleration, Maximum Velocity"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        yield deferToThread(self.aptMotor.setVelocityParameters, serial, minimumVelocity, acceleration, maximumVelocity)
        notified = self.getOtherListeners(c)
        self.onVelocityParameterChange(serial, notified)
        returnValue(True)

    @setting(7, "Get Position", returns ='v')
    def getPosition(self, c):
        """Returns Current Position"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        info = yield deferToThread(self.aptMotor.getPosition, serial)
        returnValue(info)
        
    @setting(8, "Move Relative", relativeDistance = 'v', returns ='b')
    def moveRelative(self, c, relativeDistance):
        """Moves the Motor by a Distance Relative to its Current Position"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        ok = yield deferToThread(self.aptMotor.moveRelative, serial, relativeDistance)
        notified = self.getOtherListeners(c)
        self.onPositionChange(serial, notified)
        returnValue(ok)    

    @setting(9, "Move Absolute", absolutePosition = 'v', returns ='b')
    def moveAbsolute(self, c, absolutePosition):
        """Moves the Motor an Absolute Position"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        ok = yield deferToThread(self.aptMotor.moveAbsolute, serial, absolutePosition)
        notified = self.getOtherListeners(c)
        self.onPositionChange(serial, notified)   
        returnValue(ok)    

    @setting(10, "Identify Device", returns ='b')
    def identifyDevice(self, c):
        """Identifies Device by Flashing Front Panel LED for a Few Seconds"""
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        ok = yield deferToThread(self.aptMotor.identify, serial)
        returnValue(ok)
    
    @setting(11, "Get Stage Axis Information", returns='*v')
    def getStageAxisInformation(self, c):
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        info = yield deferToThread(self.aptMotor.getStageAxisInformation, serial)
        returnValue(info)

    @setting(12, "Get Hardware Limit Switches", returns='*v')
    def getHardwareLimitSwitches(self, c):
        '''Returns the limits in the form [min, max]'''
        serial = c.get('Device', False)
        if not serial: raise Exception ("Device not selected")
        info = yield deferToThread(self.aptMotor.getHardwareLimitSwitches, serial)
        returnValue(info)
    
    def stopServer(self):  
        """Cleans up APT DLL before closing"""
        #need to check if this class has attribute aptMotor because stopSever may get called even before initServer completes
        if hasattr(self, 'aptMotor'):
            self.aptMotor.cleanUpAPT()

if __name__ == "__main__":
    from labrad import util
    util.runServer(APTMotorServer())
