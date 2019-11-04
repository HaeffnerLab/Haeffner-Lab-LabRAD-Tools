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
from labrad.units import WithUnit
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
	The following functions are called in pulse_sequence.py:
	
		abort_acquisition()
		get_acquired_data(self.N)
		get_exposure_time()
		get_trigger_mode()
		set_image_region(*self.image_region)
		set_acquisition_mode("Kinetics")
		set_exposure_time(self.initial_exposure)
		set_image_region(1, 1, 1, 658, 1, 496)
		set_number_kinetics(self.N)
		set_trigger_mode("External")
		start_acquisition()
		start_live_display()
		wait_for_kinetic()

    In addition to the functions above, the following functions are called in NuvuVideo.py:

        get_acquisition_mode
        get_detector_dimensions
        getEMCCDGain
        getemrange
        getImageRegion
        getMostRecentImage
        setEMCCDGain
        stop
        waitForAcquisition
	'''
	
    '''
    Acquisition Mode
    '''
    @setting(1, "Get Acquisition Mode", returns = 's')
    def getAcquisitionMode(self, c):
        """Gets Current Acquisition Mode"""
        return self.camera.get_acquisition_mode()
        
    @setting(2, "Set Acquisition Mode", mode = 's', returns = '')
    def setAcquisitionMode(self, c, mode):
        """Sets Current Acquisition Mode"""
        print('acquiring: {}'.format(self.setAcquisitionMode.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setAcquisitionMode.__name__))
            yield deferToThread(self.camera.set_acquisition_mode, mode)
        finally:
            print('releasing: {}'.format(self.setAcquisitionMode.__name__))
            self.lock.release()
        self.gui.set_acquisition_mode(mode)
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
            yield deferToThread(self.camera.set_trigger_mode, mode)
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
        return time #WithUnit(time, 's')
        
    @setting(6, "Set Exposure Time", expTime = 'v', returns = 'v')
    def setExposureTime(self, c, expTime):
        """Sets Current Exposure Time"""       
        print('acquiring: {}'.format(self.setExposureTime.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setExposureTime.__name__))
            yield deferToThread(self.camera.set_exposure_time, expTime)
        finally:
            print('releasing: {}'.format(self.setExposureTime.__name__))
            self.lock.release()
        #need to request the actual set value because it may differ from the request when the request is not possible
        time = self.camera.get_exposure_time()
        if c is not None:
            self.gui.set_exposure(time)
        returnValue(time) #WithUnit(time, 's'))
		
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
            yield deferToThread(self.camera.set_image, horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart, verticalEnd)
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
            yield deferToThread(self.camera.start_acquisition)
            #necessary so that start_acquisition call completes even for long kinetic series
            #yield self.wait(0.050)
            yield self.wait(0.1)
        finally:
            print('releasing: {}'.format(self.startAcquisition.__name__))
            self.lock.release()

    @setting(10, "Wait For Acquisition", returns = '')
    def waitForAcquisition(self, c):
        print 'acquiring: {}'.format(self.waitForAcquisition.__name__)
        yield self.lock.acquire()
        try:
            print 'acquired : {}'.format(self.waitForAcquisition.__name__)
            yield deferToThread(self.camera.wait_for_acquisition)
        finally:
            print 'releasing: {}'.format(self.waitForAcquisition.__name__)
            self.lock.release()
        
    @setting(11, "Abort Acquisition", returns = '')
    def abortAcquisition(self, c):
        if c is not None and self.gui.live_update_running:
            yield self.gui.stop_live_display()
        print('acquiring: {}'.format(self.abortAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.abortAcquisition.__name__))
            yield deferToThread(self.camera.abort_acquisition)
        finally:
            print('releasing: {}'.format(self.abortAcquisition.__name__))
            self.lock.release()
    
    @setting(12, "Get Acquired Data", num_images = 'i',returns = '*i')
    def getAcquiredData(self, c, num_images = 1):
        """Get the acquired images"""
        print('acquiring: {}'.format(self.getAcquiredData.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.getAcquiredData.__name__))
            image = yield deferToThread(self.camera.get_acquired_data, num_images)
        finally:
            print('releasing: {}'.format(self.getAcquiredData.__name__))
            self.lock.release()
        returnValue(image)
		
    '''
    General
    '''
    @setting(13, "Get Most Recent Image", returns = '*i')
    def getMostRecentImage(self, c):
        """Get all Data"""
        yield self.lock.acquire()
        try:
            image = yield deferToThread(self.camera.get_most_recent_image)
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
    
    @setting(16, "Get Number Kinetics", returns = 'i')
    def getNumberKinetics(self, c):
        """Gets Number Of Scans In A Kinetic Cycle"""
        return self.camera.get_number_kinetics()
     
    @setting(17, "Set Number Kinetics", numKin = 'i', returns = '')
    def setNumberKinetics(self, c, numKin):
        """Sets Number Of Scans In A Kinetic Cycle"""
        print('acquiring: {}'.format(self.setNumberKinetics.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setNumberKinetics.__name__))
            yield deferToThread(self.camera.set_number_kinetics, numKin)
        finally:
            print('releasing: {}'.format(self.setNumberKinetics.__name__))
            self.lock.release()
			
    # UPDATED THE TIMEOUT. FIX IT LATER
    @setting(18, "Wait For Kinetic", timeout = 'v', returns = 'b')
    def waitForKinetic(self, c, timeout = 20): #WithUnit(1,'s')):
        '''Waits until the given number of kinetic images are completed'''
        requestCalls = int(timeout / 0.050 ) #number of request calls
        for i in range(requestCalls):
            print('acquiring: {}'.format(self.waitForKinetic.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.waitForKinetic.__name__))
                #status = yield deferToThread(self.camera.get_status)
                #useful for debugging of how many iterations have been completed in case of missed trigger pulses
                #a,b = yield deferToThread(self.camera.get_series_progress)
                #print(a,b)
                #print(status)
            finally:
                print('releasing: {}'.format(self.waitForKinetic.__name__))
                self.lock.release()
            if status == 'DRV_IDLE':
                returnValue(True)
            yield self.wait(0.050)
        returnValue(False)
    
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
            gain = yield deferToThread(self.camera.get_emccd_gain)
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
            yield deferToThread(self.camera.set_emccd_gain, gain)
        finally:
            print 'releasing: {}'.format(self.setEMCCDGain.__name__)
            self.lock.release()
        if c is not None:
            self.gui.set_gain(gain)

    @setting(21, "getemrange", returns = '(ii)')
    def getemrange(self, c):
        #emrange = yield self.camera.get_camera_em_gain_range()
        #returnValue(emrange)
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
            dimensions = yield deferToThread(self.camera.get_detector_dimensions)
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
            #not yet created
            pass

if __name__ == "__main__":
    from labrad import util
    util.runServer(NuvuCameraServer())
	