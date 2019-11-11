#install qt4 reactor for the GUI
from NuvuVideo import NuvuVideo
from PyQt4 import QtGui
a = QtGui.QApplication([])
import qt4reactor
qt4reactor.install()
#import server libraries
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from labrad.server import LabradServer, setting, Signal
from NuvuCamera import NuvuCamera
import numpy as np

"""
### BEGIN NODE INFO
[info]
name =  Nuvu Camera Server
version = 1.0
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

class NuvuCameraServer(LabradServer):
    """ Contains methods that interact with the Nuvu Camera """
    
    name = "Nuvu Camera Server"
    
    def initServer(self):
        self.listeners = set()
        self.camera = NuvuCamera()
        self.lock = DeferredLock()
        self.gui = NuvuVideo(self)
    
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
    Trigger Mode
    '''    
    @setting(3, "Get Trigger Mode", returns = 's')
    def getTriggerMode(self, c):
        """Gets Current Trigger Mode"""
        return self.camera.get_trigger_mode()
    
    @setting(4, "Set Trigger Mode", mode = 's', returns = '')
    def setTriggerMode(self, c, mode):
        """Sets Current Trigger Mode"""
        print('acquiring: {}'.format(self.setTriggerMode.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setTriggerMode.__name__))
            self.camera.set_trigger_mode(mode)
        finally:
            print('releasing: {}'.format(self.setTriggerMode.__name__))
            self.lock.release()
        self.gui.set_trigger_mode(mode)
        
    '''
    Exposure Time
    '''
    @setting(5, "Get Exposure Time", returns = 'v')
    def getExposureTime(self, c):
        """Gets Current Exposure Time"""
        time = self.camera.get_exposure_time()
        return time
        
    @setting(6, "Set Exposure Time", expTime = 'v', returns = 'v')
    def setExposureTime(self, c, expTime):
        """Sets Current Exposure Time"""       
        print('acquiring: {}'.format(self.setExposureTime.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setExposureTime.__name__))
            self.camera.set_exposure_time(expTime)
        finally:
            print('releasing: {}'.format(self.setExposureTime.__name__))
            self.lock.release()
        #need to request the actual set value because it may differ from the request when the request is not possible
        time = self.camera.get_exposure_time()
        if c is not None:
            self.gui.set_exposure(time)
        returnValue(time)
		
    '''
    Image Region
    '''
    @setting(7, "Get Image Region", returns = '*i')
    def getImageRegion(self, c):
        """Gets Current Image Region"""
        return self.camera.get_image()
        
    @setting(8, "Set Image Region", horizontalBinning = 'i', verticalBinning = 'i', horizontalStart = 'i', horizontalEnd = 'i', verticalStart = 'i', verticalEnd = 'i', returns = '')
    def setImageRegion(self, c, horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart, verticalEnd):
        """Sets Current Image Region"""
        print('acquiring: {}'.format(self.setImageRegion.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setImageRegion.__name__))
            self.camera.set_image(horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart, verticalEnd)
        finally:
            print('releasing: {}'.format(self.setImageRegion.__name__))
            self.lock.release()

    '''
    Acquisition
    '''
    @setting(9, "Start Acquisition", returns = '')
    def startAcquisition(self, c):
        print('acquiring: {}'.format(self.startAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.startAcquisition.__name__))
            self.camera.start_acquisition()
        finally:
            print('releasing: {}'.format(self.startAcquisition.__name__))
            self.lock.release()
        
    @setting(11, "Abort Acquisition", returns = '')
    def abortAcquisition(self, c):
        if c is not None and self.gui.live_update_running:
            yield self.gui.stop_live_display()
        print('acquiring: {}'.format(self.abortAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.abortAcquisition.__name__))
            self.camera.abort_acquisition()
        finally:
            print('releasing: {}'.format(self.abortAcquisition.__name__))
            self.lock.release()
    
    @setting(12, "Get Acquired Data", timeout_in_seconds = 'i',returns = '*i')
    def getAcquiredData(self, c, timeout_in_seconds = 60):
        """Get the acquired images"""
        print('acquiring: {}'.format(self.getAcquiredData.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.getAcquiredData.__name__))
            image = self.camera.get_acquired_data(timeout_in_seconds)
        finally:
            print('releasing: {}'.format(self.getAcquiredData.__name__))
            self.lock.release()
        print('acquired data length', len(image))
        returnValue(image)
		
    '''
    General
    '''
    @setting(13, "Get Most Recent Image", returns = '*i')
    def getMostRecentImage(self, c):
        """Get most recently acquired image"""
        yield self.lock.acquire()
        try:
            image = self.camera.get_most_recent_image()
        finally:
            self.lock.release()
        returnValue(image)

    @setting(14, "Start Live Display", returns = '')
    def startLiveDisplay(self, c):
        """Starts live display of the images on the GUI"""
        yield self.gui.start_live_display()
    
    @setting(15, "Is Live Display Running", returns = 'b')
    def isLiveDisplayRunning(self, c):
        return self.gui.live_update_running
    
    @setting(16, "Get Number Images To Acquire", returns = 'i')
    def getNumberImagesToAcquire(self, c):
        """Gets Number Of Images To Acquire"""
        return self.camera.get_number_images_to_acquire()
     
    @setting(17, "Set Number Images To Acquire", numImages = 'i', returns = '')
    def setNumberImagesToAcquire(self, c, numImages):
        """Sets Number Of Images To Acquire"""
        print('acquiring: {}'.format(self.setNumberImagesToAcquire.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setNumberImagesToAcquire.__name__))
            self.camera.set_number_images_to_acquire(numImages)
        finally:
            print('releasing: {}'.format(self.setNumberImagesToAcquire.__name__))
            self.lock.release()
    
    '''
    EMCCD Gain Settings
    '''     
    @setting(19, "Get EMCCD Gain", returns = 'i')
    def getEMCCDGain(self, c):
        """Gets Current EMCCD Gain"""
        gain = None
        print 'acquiring: {}'.format(self.getEMCCDGain.__name__)
        yield self.lock.acquire()
        try:
            print 'acquired : {}'.format(self.getEMCCDGain.__name__)
            gain = self.camera.get_emccd_gain()
        finally:
            print 'releasing: {}'.format(self.getEMCCDGain.__name__)
            self.lock.release()
        if gain is not None:
            returnValue(gain)

    @setting(20, "Set EMCCD Gain", gain = 'i', returns = '')
    def setEMCCDGain(self, c, gain):
        """Sets Current EMCCD Gain"""
        print 'acquiring: {}'.format(self.setEMCCDGain.__name__)
        yield self.lock.acquire()
        try:
            print 'acquired : {}'.format(self.setEMCCDGain.__name__)
            self.camera.set_emccd_gain(gain)
        finally:
            print 'releasing: {}'.format(self.setEMCCDGain.__name__)
            self.lock.release()
        if c is not None:
            self.gui.set_gain(gain)

    @setting(21, "getemrange", returns = '(ii)')
    def getemrange(self, c):
        return self.camera.get_camera_em_gain_range()
        
    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d
    
    @setting(22, "Get Detector Dimensions", returns = 'ww')
    def get_detector_dimensions(self, c):
        print 'acquiring: {}'.format(self.get_detector_dimensions.__name__)
        yield self.lock.acquire()
        try:
            print 'acquired : {}'.format(self.get_detector_dimensions.__name__)
            dimensions = self.camera.get_detector_dimensions()
        finally:
            print 'releasing: {}'.format(self.get_detector_dimensions.__name__)
            self.lock.release()
        returnValue(dimensions)

    def stop(self):
        self._stopServer()
    
    @inlineCallbacks
    def stopServer(self):  
        """Shuts down camera before closing"""
        try:
            if self.gui.live_update_running:
                yield self.gui.stop_live_display()
            print('acquiring: {}'.format(self.stopServer.__name__))
            yield self.lock.acquire()
            print('acquired : {}'.format(self.stopServer.__name__))
            self.camera.shut_down()
            print('releasing: {}'.format(self.stopServer.__name__))
            self.lock.release()
        except Exception:
            pass

if __name__ == "__main__":
    from labrad import util
    util.runServer(NuvuCameraServer())
	