from labrad.server import LabradServer, Signal

class Signals(LabradServer):
    
    on_running_new_script = Signal(200000 , "signal_on_running_new_script", '(ws)')
    on_running_new_status = Signal(200001 , "signal_on_running_new_status", '(wsv)')
    on_running_script_paused = Signal(200002 , "signal_on_running_script_paused", 'wb')
    on_running_script_stopped = Signal(200003 , "signal_on_running_script_stopped", 'w')
    on_running_script_finished = Signal(200005 , "signal_on_running_script_finished", 'w')
    on_running_script_finished_error = Signal(200006 , "signal_on_running_script_finished_error", 'ws')
    '''
    queued scripts
    '''
    on_queued_new_script = Signal(200010 , "signal_on_queued_new_script", 'wsw')#identification, name, order
    on_queued_removed = Signal(200011 , "signal_on_queued_removed", 'w')
    '''
    scheduled script signals
    '''
    on_scheduled_new_script = Signal(200020 , "signal_on_scheduled_new_script", '(wsv)')
    on_scheduled_new_duration = Signal(200021 , "signal_on_scheduled_new_duration", 'wv')
    on_scheduled_removed = Signal(200022 , "signal_on_scheduled_removed", 'w')