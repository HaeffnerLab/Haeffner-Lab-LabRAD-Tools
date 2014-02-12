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
import sys

class script_class_parameters(object):
    '''
    storage class for information about the launchable script
    '''
    def  __init__(self, name, cls, parameters):
        self.name = name
        self.cls = cls
        self.parameters = parameters
        
class ScriptScanner(LabradServer, Signals):
    
    name = 'ScriptScanner'
    
    def initServer(self):
        self.script_parameters = {}
        self.scheduler = scheduler(Signals)
        self.load_scripts()
    
    def load_scripts(self):
        '''
        loads script information from the configuration file
        '''
        for import_path, class_name in config.scripts:
            try:
                __import__(import_path)
                module = sys.modules[import_path]
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
                try:
                    name = cls.name
                    parameters = cls.all_required_parameters()
                except AttributeError:
                    print 'Name is not provided for class {0} in module {1}'.format(class_name, module)
                else:
                    self.script_parameters[name] = script_class_parameters(name, cls, parameters)
                    
    @setting(0, "Get Available Scripts", returns = '*s')
    def get_available_scripts(self, c):
        return self.script_parameters.keys()
    
    @setting(1, "Get Script Parameters", script = 's', returns = '*(ss)')
    def get_script_parameters(self, c, script):
        if script not in self.script_parameters.keys():
            raise Exception ("Script {} Not Found".format(script))
        return self.script_parameters[script].parameters

    @setting(2, "Get Running", returns = '*(ws)')
    def get_running(self, c):
        '''
        Returns the list of currently running scripts and their IDs.
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
    
    @setting(5, "Remove Queued Script", script_ID = 'w')
    def remove_queued_script(self, c, script_ID):
        self.scheduler.remove_queued_script(script_ID)
    
    @setting(6, "Get Progress", script_ID = 'w', returns = 'sv')
    def get_progress(self, c, script_ID):
        '''
        Get progress of a currently running experiment
        '''
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to get progress of script with ID {0} but it was not running".format(script_ID))
        return status.get_progress()
    
    @setting(10, 'New Experiment', script_name = 's', returns = 'w')
    def new_script(self, c, script_name):
        '''
        Launch script. Returns ID of the queued scan.
        '''
        if script_name not in self.script_parameters.keys():
            raise Exception ("Script {} Not Found".format(script_name))
        script = self.script_parameters[script_name]
        single_launch = scan_methods.single(script.cls)
        scan_id = self.scheduler.add_scan_to_queue(single_launch)
        return scan_id
    
    @setting(11, "New Script Repeat", script_name = 's', repeat = 'w', save_data = 'b')
    def new_script_repeat(self, c, script_name, repeat, save_data = True):
        if script_name not in self.script_parameters.keys():
            raise Exception ("Script {} Not Found".format(script_name))
        script = self.script_parameters[script_name]
        repeat_launch = scan_methods.repeat_reload(script.cls, repeat, save_data)
        scan_id = self.scheduler.add_scan_to_queue(repeat_launch)
        return scan_id
    
    @setting(12, "New Script Scan", scan_script_name = 's', measure_script_name = 's', collection = 's', parameter_name = 's', minim = 'v', maxim = 'v', steps = 'w', units = 's')
    def new_scan(self, c, scan_script_name, measure_script_name, collection, parameter_name, minim, maxim, steps, units):
        #need error checking that parmaters are valid
        if scan_script_name not in self.script_parameters.keys():
            raise Exception ("Script {} Not Found".format(scan_script_name))
        if measure_script_name not in self.script_parameters.keys():
            raise Exception ("Script {} Not Found".format(measure_script_name))
        scan_script = self.script_parameters[scan_script_name]
        measure_script = self.script_parameters[measure_script_name]
        parameter = (collection,parameter_name)
        if scan_script == measure_script:
            scan_launch = scan_methods.scan_experiment_1D(scan_script.cls, parameter, minim, maxim, steps, units)
        else:
            scan_launch = scan_methods.scan_experiment_1D_measure(scan_script.cls, measure_script.cls, parameter, minim, maxim, steps, units)
        scan_id = self.scheduler.add_scan_to_queue(scan_launch)
        return scan_id
    
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
    
    @setting(15, 'Cancel Scheduled Script', scheduled_ID = 'w')
    def cancel_scheduled_script(self, c, scheduled_ID):
        '''
        Cancel the currently scheduled script
        '''
        self.scheduler.cancel_scheduled_script(scheduled_ID)
    
    @setting(20, "Pause Script", script_ID = 'w', should_pause = 'b')
    def pause_script(self, c, script_ID, should_pause):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to pause script with ID {0} but it was not running".format(script_ID))
        status.set_pausing(should_pause)
        
    @setting(21, "Stop Script", script_ID = 'w')
    def stop_script(self, c, script_ID):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to stop script with ID {0} but it was not running".format(script_ID))
        status.set_stopping()

    @setting(30, "Register External Launch", name = 's', returns = 'w')
    def register_external_launch(self, c, name):
        '''
        Issues a running ID to a script that is launched externally and not through this server. The external script
        can then update its status, be paused or stopped.
        '''
        external_scan = scan_methods.experiment_info(name)
        ident = self.scheduler.add_external_scan(external_scan)
        return ident
    
    @setting(31, "Script Set Progress", script_ID = 'w', progress = 'v')
    def script_set_progress(self, c, script_ID, progress):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to set progress of script with ID {0} but it was not running".format(script_ID))
        status.set_percentage(progress)
    
    @setting(32, "Launch Confirmed", script_ID = 'w')
    def launch_confirmed(self, c, script_ID):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to confirm launch of script with ID {0} but it was not running".format(script_ID))
        status.launch_confirmed()
    
    @setting(33, "Finish Confirmed", script_ID = 'w')
    def finish_confirmed(self, c, script_ID):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to confirm Finish of script with ID {0} but it was not running".format(script_ID))
        status.finish_confirmed()
        self.scheduler.remove_if_external(script_ID)
    
    @setting(34, "Stop Confirmed", script_ID = 'w')
    def stop_confiromed(self, c, script_ID):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to confirm Stop of script with ID {0} but it was not running".format(script_ID))
        status.stop_confirmed()

    @setting(35,"Pause Or Stop", script_ID = 'w', returns = 'b')
    def pause_or_stop(self, c, script_ID):
        '''
        Returns the boolean whether or not the script should be stopped. This request blocks while the script is to be paused.
        '''
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to confirm Pause/Stop of script with ID {0} but it was not running".format(script_ID))
        yield status.pause()
        returnValue(status.should_stop)
    
    @setting(36, "Error Finish Confirmed", script_ID = 'w', error_message = 's')
    def error_finish_confirmed(self, c, script_ID, error_message):
        status = self.scheduler.get_running_status(script_ID)
        if status is None:
            raise Exception ("Trying to confirm error finish of script with ID {0} but it was not running".format(script_ID))
        status.error_finish_confirmed(error_message)
        self.scheduler.remove_if_external(script_ID)

    @inlineCallbacks
    def stopServer(self):
        '''
        stop all the running scripts and exit
        '''
        yield None
        try:
            #cancel all scheduled scripts
            for scheduled,name,loop in self.scheduler.get_scheduled():
                self.scheduler.cancel_scheduled_script(scheduled)
            for ident, scan, priority in self.scheduler.get_queue():
                self.scheduler.remove_queued_script(ident)
            #stop all running scipts
            for ident, name in self.scheduler.get_running():
                self.scheduler.stop_running(ident)
            #wait for all deferred to finish
            running = DeferredList(self.scheduler.running_deferred_list())
            yield running
        except AttributeError:
            #if dictionary doesn't exist yet (i.e bad identification error), do nothing
            pass

if __name__ == "__main__":
    from labrad import util
    util.runServer( ScriptScanner() )