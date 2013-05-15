#install qt4 reactor for the GUI
from AndorVideo import AndorVideo
from PyQt4 import QtGui
a = QtGui.QApplication( [])
import qt4reactor
qt4reactor.install()
#import server libraries
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from labrad.server import LabradServer, setting
from AndorCamera import AndorCamera
from labrad.units import WithUnit

"""
### BEGIN NODE INFO
[info]
name =  Andor Server
version = 0.9
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

class AndorServer(LabradServer):
    """ Contains methods that interact with the Andor CCD Cameras"""
    
    name = "Andor Server"
    
    def initServer(self):
        self.listeners = set()
        self.camera = AndorCamera()
        self.lock = DeferredLock()
        self.gui = AndorVideo(self)
    
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
        
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified
    '''
    Temperature Related Settings
    '''
    @setting(0, "Get Temperature", returns = 'v[degC]')
    def get_temperature(self, c):
        """Gets Current Device Temperature"""
        temperature = None
        yield self.lock.acquire()
        try:
            temperature  = yield deferToThread(self.camera.get_temperature)
        finally:
            self.lock.release()
        if temperature is not None:
            temperature = WithUnit(temperature, 'degC')
            returnValue(temperature)

    @setting(1, "Get Cooler State", returns = 'b')
    def get_cooler_state(self, c):
        """Returns Current Cooler State"""
        cooler_state = None
        yield self.lock.acquire()
        try:
            cooler_state = yield deferToThread(self.camera.get_cooler_state)
        finally:
            self.lock.release()
        if cooler_state is not None:
            returnValue(cooler_state)
        
    @setting(3, "Set Temperature", setTemp = 'v[degC]', returns = '')
    def set_temperature(self, c, setTemp):
        """Sets The Target Temperature"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_temperature, setTemp['degC'])
        finally:
            self.lock.release()
        
    @setting(4, "Set Cooler On", returns = '')
    def set_cooler_on(self, c):
        """Turns Cooler On"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_cooler_on)
        finally:
            self.lock.release()
    
    @setting(5, "Set Cooler Off", returns = '')
    def set_cooler_off(self, c):
        """Turns Cooler On"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_cooler_off)
        finally:
            self.lock.release()
    
    '''
    EMCCD Gain Settings
    '''     
    @setting(6, "Get EMCCD Gain", returns = 'i')
    def getEMCCDGain(self, c):
        """Gets Current EMCCD Gain"""
        gain = None
        yield self.lock.acquire()
        try:
            gain = yield deferToThread(self.camera.get_emccd_gain)
        finally:
            self.lock.release()
        if gain is not None:
            returnValue(gain)

    @setting(7, "Set EMCCD Gain", gain = 'i', returns = '')
    def setEMCCDGain(self, c, gain):
        """Sets Current EMCCD Gain"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_emccd_gain, gain)
        finally:
            self.lock.release()
        if c is not None:
            self.gui.set_gain(gain)
    '''
    Read mode
    '''        
    @setting(8, "Get Read Mode", returns = 's')
    def getReadMode(self, c):
        return self.camera.get_read_mode()

    @setting(9, "Set Read Mode", readMode = 's', returns = '')
    def setReadMode(self, c, readMode):
        """Sets Current Read Mode"""
        mode = None
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_read_mode, readMode)
        finally:
            self.lock.release()
        if mode is not None:
            returnValue(mode)
    '''
    Acquisition Mode
    '''
    @setting(10, "Get Acquisition Mode", returns = 's')
    def getAcquisitionMode(self, c):
        """Gets Current Acquisition Mode"""
        return self.camera.get_acquisition_mode()
        
    @setting(11, "Set Acquisition Mode", mode = 's', returns = '')
    def setAcquisitionMode(self, c, mode):
        """Sets Current Acquisition Mode"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_acquisition_mode, mode)
        finally:
            self.lock.release()
    
    '''
    Trigger Mode
    '''    
    @setting(12, "Get Trigger Mode", returns = 's')
    def getTriggerMode(self, c):
        """Gets Current Trigger Mode"""
        return self.camera.get_trigger_mode()
    
    @setting(13, "Set Trigger Mode", mode = 's', returns = '')
    def setTriggerMode(self, c, mode):
        """Sets Current Trigger Mode"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_trigger_mode, mode)
        finally:
            self.lock.release()
    '''
    Exposure Time
    '''
    @setting(14, "Get Exposure Time", returns = 'v[s]')
    def getExposureTime(self, c):
        """Gets Current Exposure Time"""
        time = self.camera.get_exposure_time()
        return WithUnit(time, 's')
        
    @setting(15, "Set Exposure Time", expTime = 'v[s]', returns = 'v[s]')
    def setExposureTime(self, c, expTime):
        """Sets Current Exposure Time"""       
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_exposure_time, expTime['s'])
        finally:
            self.lock.release()
        #need to request the actual set value because it may differ from the request when the request is not possible
        time = self.camera.get_exposure_time()
        if c is not None:
            self.gui.set_exposure(time)
        returnValue(WithUnit(time, 's'))
    '''
    Image Region
    '''
    @setting(16, "Get Image Region", returns = '*i')
    def getImageRegion(self, c):
        """Gets Current Image Region"""
        return self.camera.get_image()
        
    @setting(17, "Set Image Region", horizontalBinning = 'i', verticalBinning = 'i', horizontalStart = 'i', horizontalEnd = 'i', verticalStart = 'i', verticalEnd = 'i', returns = '')
    def setImageRegion(self, c, horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart, verticalEnd):
        """Sets Current Image Region"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_image, horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart, verticalEnd)
        finally:
            self.lock.release()
    '''
    Acquisition
    '''
    @setting(18, "Start Acquisition", returns = '')
    def startAcquisition(self, c):
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.start_acquisition)
        finally:
            self.lock.release()

    @setting(19, "Wait For Acquisition", returns = '')
    def waitForAcquisition(self, c):
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.wait_for_acquisition)
        finally:
            self.lock.release()
        
    @setting(20, "Abort Acquisition", returns = '')
    def abortAcquisition(self, c):
        if c is not None and self.gui.live_update_running:
            yield self.gui.stop_live_display()
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.abort_acquisition)
        finally:
            self.lock.release()
    
    @setting(21, "Get Acquired Data", num_images = 'i',returns = '*i')
    def getAcquiredData(self, c, num_images = 1):
        """Get the acquired images"""
        yield self.lock.acquire()
        try:
            image = yield deferToThread(self.camera.get_acquired_data, num_images)
        finally:
            self.lock.release()
        returnValue(image)

    '''
    General
    '''
    @setting(22, "Get Camera Serial Number", returns = 'i')
    def getCameraSerialNumber(self, c):
        """Gets Camera Serial Number"""
        return self.camera.get_camera_serial_number()
    
    @setting(23, "Get Most Recent Image", returns = '*i')
    def getMostRecentImage(self, c):
        """Get all Data"""
        yield self.lock.acquire()
        try:
            image = yield deferToThread(self.camera.get_most_recent_image)
        finally:
            self.lock.release()
        returnValue(image)
    
    @setting(24, "Start Live Display", returns = '')
    def startLiveDisplay(self, c):
        """Get all Data"""
        yield self.gui.start_live_display()
    
    @setting(25, "Get Number Kinetics", returns = 'i')
    def getNumberKinetics(self, c):
        """Gets Number Of Scans In A Kinetic Cycle"""
        return self.camera.get_number_kinetics()
     
    @setting(26, "Set Number Kinetics", numKin = 'i', returns = '')
    def setNumberKinetics(self, c, numKin):
        """Sets Number Of Scans In A Kinetic Cycle"""
        yield self.lock.acquire()
        try:
            yield deferToThread(self.camera.set_number_kinetics, numKin)
        finally:
            self.lock.release()
    
    @setting(27, "Wait For Kinetic", timeout = 'v[s]',returns = 'b')
    def waitForKinetic(self, c, timeout = WithUnit(10,'s')):
        '''Waits until the given number of kinetic images are completed'''
        requestCalls = int(timeout['s'] / 0.050 ) #number of request calls
        for i in range(requestCalls):
            yield self.lock.acquire()
            try:
                status = yield deferToThread(self.camera.get_status)
            finally:
                self.lock.release()
            if status == 'DRV_IDLE':
                returnValue(True)
            yield self.wait(0.050)
        returnValue(False)
        
    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d

    def stop(self):
        self._stopServer()
    
    @inlineCallbacks
    def stopServer(self):  
        """Shuts down camera before closing"""
        try:
            if self.gui.live_update_running:
                yield self.gui.stop_live_display()
            yield self.lock.acquire()
            self.camera.shut_down()
            self.lock.release()
        except Exception:
            #not yet created
            pass

if __name__ == "__main__":
    from labrad import util
    util.runServer(AndorServer())