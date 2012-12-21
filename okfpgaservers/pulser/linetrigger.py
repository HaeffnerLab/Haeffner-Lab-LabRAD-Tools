from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread
from hardwareConfiguration import hardwareConfiguration

class LineTrigger(LabradServer):
    
    """Contains the Line Trigger Functionality for the Pulser Server"""
    
    on_line_trigger_param = Signal(142007, 'signal: new line trigger parameter', '(bv)')
    
    @setting(60, "Get Line Trigger Limits", returns = '*2v[us]')
    def getLineTriggerLimits(self, c):
        """get limits for duration of line triggering"""
        return hardwareConfiguration.lineTriggerLimits
    
    @setting(61, "Enable Line Trigger", enable = 'b', offset_duration = 'v[us]', returns = 'b')
    def enableLineTrigger(self, c, enable, offset_duration = None):
        """enable or disable line triggering. if enabling, can specify the offset_duration"""
        if enable:
            #set duration and run
            if offset_duration is not None:
                offset_duration = int(offset_duration['us'])
            else:
                offset_duration = 0
            yield self.inCommunication.run(self._enableLineTrigger, offset_duration)
        else:
            #disabling
            yield self.inCommunication.run(self._disableLineTrigger)
        #emit signal that value has been changed
        self.notifyOtherListeners(c, (enable, offset_duration), self.on_line_trigger_param)
        returnValue(enable)
            
    @inlineCallbacks   
    def _enableLineTrigger(self, delay):
        yield deferToThread(self.api.enableLineTrigger, delay)
    
    @inlineCallbacks
    def _disableLineTrigger(self):
        yield deferToThread(self.api.disableLineTrigger)