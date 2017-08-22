'''
### BEGIN NODE INFO
[info]
name = ScriptScanner
version = 0.9
description =
instancename = ScriptScanner

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
'''
from labrad.server import LabradServer, setting
from labrad.units import WithUnit
from twisted.internet.defer import inlineCallbacks, DeferredList, returnValue
from signals import Signals
from configuration import config
import scan_methods
from scheduler import scheduler
from parameter_vault import ParameterVault
from sequence_wrapper import pulse_sequence_wrapper as psw
from multi_sequence_wrapper import multi_sequence_wrapper
import sys
        
class ScriptScanner(ParameterVault, Signals, LabradServer):
    
    name = 'ScriptScanner'
    
    @inlineCallbacks
    def initServer(self):
        """Load all of the paramters from the registry."""
        self.listeners = set()
        self.parameters = {}  
        yield self.load_parameters()

        self.sequences = {} # dict mapping sequence names to modules
        self.scheduler = scheduler(Signals, self)
        self.load_sequences()
    
    def load_sequences(self):
        '''
        loads sequence information from the configuration file
        
        TODO: configuration file should just specify path to
        the sequence folder, then just import all the sequences
        in that folder
        '''
        self.modules = [] # collection of modules for reloading
        for import_path, class_name in config.sequences:
            #print import_path, class_name
            try:
                __import__(import_path)
                module = sys.modules[import_path]
                self.modules.append(module)
                cls = getattr(module, class_name)
            except ImportError as e:
                print 'Script Control Error importing: ', e
            except AttributeError:
                print 'There is no class {0} in module {1}'.format(class_name, module) 
            except SyntaxError as e:
                print 'Incorrect syntax in file {0}'.format(import_path, class_name)
            except Exception as e:
                print 'There was an error in {0} : {1}'.format(class_name, e)
            else:
                name = cls.__name__
                self.sequences[name] = cls
                    
    @setting(0, "Get Available Sequences", returns = '*s')
    def get_available_sequences(self, c):
        return self.sequences.keys()

    @setting(2, "Get Running", returns = '*(ws)')
    def get_running(self, c):
        '''
        Returns the list of currently running sequences and their IDs.
        '''
        return self.scheduler.get_running()
    
    @setting(3, "Get Scheduled", returns ='*(wsv[s])')
    def get_scheduled(self, c):
        '''
        Returns the list of currently scheduled scans with their IDs and durtation
        '''
        scheduled = self.scheduler.get_scheduled()
        scheduled = [(ident, name, WithUnit(dur,'s') ) for (ident, name, dur) in scheduled]
        return scheduled
    
    @setting(4, "Get Queue", returns = '*(wsw)')
    def get_queue(self, c):
        '''
        Returns the current queue of scans in the form ID / Name / order
        '''
        return self.scheduler.get_queue()
    
    @setting(5, "Remove Queued Sequence", sequence_ID = 'w')
    def remove_queued_sequence(self, c, sequence_ID):
        self.scheduler.remove_queued_script(sequence_ID)
    
    @setting(6, "Get Progress", sequence_ID = 'w', returns = 'sv')
    def get_progress(self, c, sequence_ID):
        '''
        Get progress of a currently running experiment
        '''
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to get progress of sequence with ID {0} but it was not running".format(sequence_ID))
        return status.get_progress()

    @setting(10, 'New Sequence', sequence_name = 's', settings = '*(svvis)', returns = 'w')
    def new_sequence(self, c, sequence_name, settings):
        '''
        Launch a new sequence. Returns ID of the queued scan.
        settings = [scan param, minim, maxim, steps, unit]
        '''
        print "LAUNCHING A NEW SEQUENCE"
        if sequence_name not in self.sequences.keys():
            raise Exception ("Sequence {} Not Found".format(sequence_name))

        cls = self.sequences[sequence_name]
        
        if not cls.is_composite:
            print "running a single scan"
            scan_param, m1, m2, steps, unit = settings[0]
            wrapper = psw(cls, self, self.client)
            if scan_param == 'None':
                wrapper.set_scan_none()
            else:
                wrapper.set_scan(scan_param, m1, m2, steps, unit)
                
        else: # this is for composite sequences
            print "running a composite scan"
            wrapper = multi_sequence_wrapper(cls, self, self.client)
            wrapper.set_scan(settings)
            
        scan_id = self.scheduler.add_scan_to_queue(wrapper)
        print scan_id
        return scan_id

    @setting(12, 'New Sequence Schedule', sequence_name = 's', settings = '(svvis)', duration = 'v[s]', priority = 's', start_now = 'b', returns = 'w')
    def new_sequence_schedule(self, c, sequence_name, settings,  duration, priority, start_now):
        '''
        Schedule the script to run every spcified duration of seconds.
        Priority indicates the priority with which the scrpt is scheduled.
        '''
        if sequence_name not in self.sequences.keys():
            raise Exception ("Sequence {} Not Found".format(sequence_name))
        if priority not in ['Normal','First in Queue','Pause All Others']:
            raise Exception ("Priority not recognized")
        scan_param, m1, m2, steps, unit = settings
        cls = self.sequences[sequence_name]
        wrapper = psw(cls, self, self.client)
        if scan_param == 'None':
            raise Exception ('Scheduled sequences must have a scan parameter')
        wrapper.set_scan(scan_param, m1, m2, steps, unit)
        schedule_id = self.scheduler.new_scheduled_scan(wrapper, duration['s'], priority, start_now)
        print schedule_id
        return schedule_id
    
    @setting(13, 'New Script Schedule', script_name = 's', duration = 'v[s]', priority = 's', start_now = 'b', returns ='w')
    def new_script_schedule(self, c, script_name, duration, priority = 'Normal', start_now = True):
        '''
        Schedule the script to run every spcified duration of seconds.
        Priority indicates the priority with which the scrpt is scheduled.
        '''
        if script_name not in self.script_parameters.keys():
            raise Exception ("Script {} Not Found".format(script_name))
        if priority not in ['Normal','First in Queue','Pause All Others']:
            raise Exception ("Priority not recognized")
        script = self.script_parameters[script_name]
        single_launch = scan_methods.single(script.cls)
        schedule_id = self.scheduler.new_scheduled_scan(single_launch, duration['s'], priority, start_now)
        return schedule_id
    
    @setting(14, 'Change Scheduled Duration', scheduled_ID = 'w', duration = 'v[s]')
    def change_scheduled_duration(self, c, scheduled_ID, duration):
        '''
        Change duration of the scheduled script executation
        '''
        self.scheduler.change_period_scheduled_script(scheduled_ID, duration['s'])
    
    @setting(15, 'Cancel Scheduled Sequence', scheduled_ID = 'w')
    def cancel_scheduled_sequence(self, c, scheduled_ID):
        '''
        Cancel the currently scheduled sequence
        '''
        self.scheduler.cancel_scheduled_script(scheduled_ID)
    
    @setting(20, "Pause Sequence", sequence_ID = 'w', should_pause = 'b')
    def pause_sequence(self, c, sequence_ID, should_pause):
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to pause sequence with ID {0} but it was not running".format(sequence_ID))
        status.status = 'Pausing'
        #status.set_pausing(should_pause)
        
    @setting(21, "Stop Sequence", sequence_ID = 'w')
    def stop_sequence(self, c, sequence_ID):
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to stop sequence with ID {0} but it was not running".format(sequence_ID))
        status.set_stopping()

    @setting(30, "Register External Launch", name = 's', returns = 'w')
    def register_external_launch(self, c, name):
        '''
        Issues a running ID to a sequence that is launched externally and not through this server. The external
        sequence can then update its status, be paused or stopped.
        '''
        external_scan = scan_methods.experiment_info(name)
        ident = self.scheduler.add_external_scan(external_scan)
        return ident
    
    @setting(31, "Sequence Set Progress", sequence_ID = 'w', progress = 'v')
    def sequence_set_progress(self, c, sequence_ID, progress):
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to set progress of sequence with ID {0} but it was not running".format(sequence_ID))
        status.set_percentage(progress)
    
    @setting(32, "Launch Confirmed", sequence_ID = 'w')
    def launch_confirmed(self, c, sequence_ID):
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to confirm launch of sequence with ID {0} but it was not running".format(sequence_ID))
        status.launch_confirmed()
    
    @setting(33, "Finish Confirmed", sequence_ID = 'w')
    def finish_confirmed(self, c, sequence_ID):
        self._finish_confirmed(sequence_ID)

    #@inlineCallbacks
    def _finish_confirmed(self, sequence_ID):
        print "finishing up"
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to confirm Finish of sequence with ID {0} but it was not running".format(sequence_ID))
        status.finish_confirmed()
        self.scheduler.remove_if_external(sequence_ID)
    
    @setting(34, "Stop Confirmed", sequence_ID = 'w')
    def stop_confirmed(self, c, sequence_ID):
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to confirm Stop of sequence with ID {0} but it was not running".format(sequence_ID))
        status.stop_confirmed()

    @setting(35,"Pause Or Stop", sequence_ID = 'w', returns = 'b')
    def pause_or_stop(self, c, sequence_ID):
        '''
        Returns the boolean whether or not the sequence should be stopped. This request blocks while the sequence is to be paused.
        '''
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to confirm Pause/Stop of sequence with ID {0} but it was not running".format(sequence_ID))
        yield status.pause()
        returnValue(status.should_stop)

    #@inlineCallbacks
    def _pause_or_stop(self, sequence_ID):
        '''
        Returns the boolean whether or not the sequence should be stopped. This request blocks while the sequence is to be paused.
        '''
        print "pause or stop"
        status = self.scheduler.get_running_status(sequence_ID)
        print "status.status: {}".format(status.status)
        if status is None:
            raise Exception ("Trying to confirm Pause/Stop of sequence with ID {0} but it was not running".format(sequence_ID))
        status.pause()
        return status.should_stop

    def _should_pause(self, sequence_ID):
        pass
        status = self.scheduler.get_running_status(sequence_ID)
        #print status.status
    
    @setting(36, "Error Finish Confirmed", sequence_ID = 'w', error_message = 's')
    def error_finish_confirmed(self, c, sequence_ID, error_message):
        status = self.scheduler.get_running_status(sequence_ID)
        if status is None:
            raise Exception ("Trying to confirm error finish of sequence with ID {0} but it was not running".format(sequence_ID))
        status.error_finish_confirmed(error_message)
        self.scheduler.remove_if_external(sequence_ID)

    @setting(37, "Get Sequence Scannables", sequence = 's', returns = '*(s(vvis))')
    def get_sequence_scannables(self, c, sequence):
        try:
            scan = self.sequences[sequence].scannable_params.items()
            li = []
            for item in scan:
                li.append((item[0], item[1][0]))
            return li
            #return self.sequences[sequence].scannable_params.items()
        except KeyError:
            raise Exception('Sequence not found')

    @setting(38, "Get Preferred Parameters", sequence = 's', returns = '*s')
    def get_preferred_parameters(self, c, sequence):
        try:
            return self.sequences[sequence].show_params
        except KeyError:
            raise Exception('Sequence not found')

    @setting(39, 'Reload sequences', returns = '')
    def reload_sequences(self, c):
        '''
        Reload all sequences so that sequence changes are reflected
        in the script scanner
        '''
        for m in self.modules: reload(m)
        self.load_sequences()

    @inlineCallbacks
    def stopServer(self):
        '''
        stop all the running sequence and exit
        '''
        yield None
        try:
            #cancel all scheduled sequences
            for scheduled,name,loop in self.scheduler.get_scheduled():
                self.scheduler.cancel_scheduled_script(scheduled)
            for ident, scan, priority in self.scheduler.get_queue():
                self.scheduler.remove_queued_script(ident)
            #stop all running sequences
            for ident, name in self.scheduler.get_running():
                self.scheduler.stop_running(ident)
            #wait for all deferred to finish
            running = DeferredList(self.scheduler.running_deferred_list())
            yield running
            #yield self.save_parameters()
        except AttributeError:
            #if dictionary doesn't exist yet (i.e bad identification error), do nothing
            pass

if __name__ == "__main__":
    from labrad import util
    util.runServer( ScriptScanner() )
