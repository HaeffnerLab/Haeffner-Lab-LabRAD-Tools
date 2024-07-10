from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread
from hardwareConfiguration import hardwareConfiguration
from labrad.units import WithUnit

class LineTrigger(LabradServer):
    
    """Contains the Line Trigger Functionality for the Pulser Server"""
    
    on_line_trigger_param = Signal(142007, 'signal: new line trigger parameter', '(bv)')
    
    def initialize(self):
        self.linetrigger_enabled = False
        self.linetrigger_duration = WithUnit(0, 'us')
        self.linetrigger_limits = [WithUnit(v, 'us') for v in hardwareConfiguration.lineTriggerLimits]
        
    @setting(60, "Get Line Trigger Limits", returns = '*v[us]')
    def getLineTriggerLimits(self, c):
        """get limits for duration of line triggering"""
        return (self.linetrigger_limits )
        
    @setting(61, 'Line Trigger State', enable = 'b',returns = 'b')
    def line_trigger_state(self, c, enable = None):
        if enable is not None:
            if enable:
                yield self.inCommunication.run(self._enableLineTrigger, self.linetrigger_duration)
            else:
                yield self.inCommunication.run(self._disableLineTrigger)
            self.linetrigger_enabled = enable
            self.notifyOtherListeners(c, (self.linetrigger_enabled, self.linetrigger_duration), self.on_line_trigger_param)
        returnValue (self.linetrigger_enabled)
    
    @setting(62, "Line Trigger Duration", duration = 'v[us]', returns = 'v[us]')
    def line_trigger_duration(self, c, duration = None):
        """enable or disable line triggering. if enabling, can specify the offset_duration"""
        if duration is not None:
            if self.linetrigger_enabled:
                yield self.inCommunication.run(self._enableLineTrigger, duration)
            self.linetrigger_duration = duration
            self.notifyOtherListeners(c, (self.linetrigger_enabled, self.linetrigger_duration), self.on_line_trigger_param)
        returnValue (self.linetrigger_duration)
            
    @inlineCallbacks   
    def _enableLineTrigger(self, delay):
        delay = int(delay['us'])
        yield deferToThread(self.api.enableLineTrigger, delay)
    
    @inlineCallbacks
    def _disableLineTrigger(self):
        yield deferToThread(self.api.disableLineTrigger)