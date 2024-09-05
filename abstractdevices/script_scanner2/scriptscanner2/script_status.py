from twisted.internet.defer import inlineCallbacks, DeferredLock, Deferred
from threading import Lock
from signals import Signals


'''
script_semaphore defines a class used to store runtime behavior information
about a script that is ready, running, paused, stopped, or finished.

Class attributes
================

pause_lock: A Lock object which is used to prevent execution of a script
            that has been placed in "Paused" status. See comments on the
            pause() method for more details on how this lock is used.

pause_requests: A list of callbacks to notify when a requested pause has
                been completed, i.e., when the script has moved from the
                "Pausing" status to the "Paused" status.

continue_requests: A list of callbacks to notify when a requested continue
                   has been completed, i.e., when the script has moved from
                   the "Pausing" or "Paused" status back to "Running".

status: A script_semaphore object can have the following status values:
    - "Ready":    Script object has been created but has not yet started.
    - "Running":  Script is currently executing.
    - "Pausing":  Pause has been requested. Script is still running but will be
                  paused at the next opportunity.
    - "Paused":   Script was previously started but is currently paused.
    - "Stopping": Stop has been requested. Script is still running but will be
                  stopped at the next opportunity.
    - "Stopped":  Script was previously started, but has been terminated early.
    - "Finished": Script ran to completion and has finished executing.
    - "Error":    Unexpected exception occurred during script execution. Details
                  should have been printed to the console.

percentage_complete: A float whose value must be between 0.0 and 100.0.
                     Indicates the completion progress of the script.

should_stop: Indicates whether a stop has been requested, i.e., if the script has
             been placed into the "Stopping" state. This is reset to False once
             the script has been moved to "Stopped".
             [TO DO - Is this just equivalent to (status == "Stopping")? If so, delete it?]

ident: The script identifier passed by the scheduler. Typically just an integer from
       a counter that indicates the order in which the scripts have been started.

signals: An object to allow script_semaphore to notify subscribers on various events.
'''

class script_semaphore(object):
    def __init__(self, ident, signals):
        self.pause_lock = Lock()
        self.pause_requests = []
        self.continue_requests = []
        self.already_called_continue = False # [TO DO - This is unused - delete?]

        self.status = 'Ready'
        self.percentage_complete = 0.0
        self.should_stop = False
        self.ident = ident
        self.signals = signals
        
    def get_progress(self):
        return (self.status, self.percentage_complete)
    
    def set_percentage(self, perc):
        if not 0.0 <= perc <= 100.0: raise Exception ("Incorrect Percentage of Completion")
        #print 'percentage complete =', perc
        self.percentage_complete = perc

        self.status = 'Running'

        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
    
    def launch_confirmed(self):
        self.status = 'Running'
        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))

    def pause(self):
        '''

        pause() is typically called by script_scanner after the collection of each
        data point, to see if the script needs to be paused or not.

        When a pause is requested (i.e., when set_pausing is called), the script is
        placed into "Pausing" status and the pause_lock is acquired by set_pausing.
        At the next time pause() is called, if the pause_lock is currently acquired,
        the script is placed into the "Paused" status. pause() then makes a blocking
        acquisition of pause_lock, to be released immediately thereafter. So pause()
        will not return until pause_lock has been released, which occurs whenever
        the script is requested to be either continued or stopped.

        '''
        if self.pause_lock.locked():
            self.status = 'Paused'
            self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
            self.signals.on_running_script_paused((self.ident, True))
            #call back all pause requests
            while self.pause_requests:
                request = self.pause_requests.pop()
                print 'called back pause requests', request
                request.callback(True)
        print 'script checking on whether should pause'
        self.pause_lock.acquire()
        self.pause_lock.release()
        print 'script proceeding'
        if self.status == 'Paused' or self.status == 'Pausing':
            self.status = 'Running'
            self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
            self.signals.on_running_script_paused((self.ident, False))
            #call back all continue requests
            while self.continue_requests:
                request = self.continue_requests.pop()
                request.callback(True)
        
    @inlineCallbacks
    def pause_inline(self):
        '''
        gets called by the script to pause.
        '''
        if self.pause_lock.locked():
            self.status = 'Paused'
            self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
            self.signals.on_running_script_paused((self.ident, True))
            #call back all pause requests
            while self.pause_requests:
                request = self.pause_requests.pop()
                print 'called back pause requests', request
                request.callback(True)
        print 'script checking on whether should pause'
        yield self.pause_lock.acquire()
        self.pause_lock.release()
        print 'script proceeding'

        if self.status == 'Paused' or self.status == 'Pausing':

            self.status = 'Running'
            self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
            self.signals.on_running_script_paused((self.ident, False))
            #call back all continue requests
            while self.continue_requests:
                request = self.continue_requests.pop()
                request.callback(True)

    def set_stopping(self):
        self.should_stop = True
        self.status = 'Stopping'
        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
        #if was paused, unpause:
        if self.pause_lock.locked():
            self.pause_lock.release()
    
    def set_pausing(self, should_pause):

        '''
        Called to request that a script be paused (should_pause==True) or continued
        (should_pause==False). This does not actually pause the script -- it simply
        creates a pause request that will be honored next time pause() is called.

        If asking to pause, returns a Deferred which is called back after the script
        has actually been paused.

        If asking to continue, returns a Deferred which is called back after the script
        has been unpaused and is running again.
        '''

        if should_pause:
            request = Deferred()
            print 'made pause request', request
            self.pause_requests.append(request)
            if not self.pause_lock.locked():
                #if not already paused
                self.pause_lock.acquire()
                self.status = 'Pausing'
                self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
                #print 'acquired pause', request

            else:
                print 'not acquiring because locked'
        else:
            if not self.pause_lock.locked():
                raise Exception ("Trying to unpause script that was not paused")
            request = Deferred()
            print 'made continue request', request
            self.continue_requests.append(request)
            #print 'releasing the lock!'

            self.pause_lock.release()
        return request
            
    def stop_confirmed(self):
        self.should_stop = False
        self.status = 'Stopped'
        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
        self.signals.on_running_script_stopped(self.ident)
    
    def finish_confirmed(self):
        #call back all pause requests
        for request_list in [self.pause_requests, self.continue_requests]:
            while(request_list):
                request = request_list.pop()
                request.callback(True)
        if not self.status == 'Stopped':
            self.percentage_complete = 100.0
            self.status = 'Finished'
            self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
        self.signals.on_running_script_finished(self.ident)
    
    def error_finish_confirmed(self, error):
        self.status = 'Error'
        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
        self.signals.on_running_script_finished_error((self.ident, error))