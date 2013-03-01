from twisted.internet.defer import inlineCallbacks, DeferredLock, Deferred
from signals import Signals

class script_semaphore(object):
    '''class for storing information about runtime behavior script'''
    def __init__(self, ident, signals):
        self.pause_lock = DeferredLock()
        self.pause_requests = []
        self.continue_requests = []
        self.already_called_continue = False
        self.status = 'Ready'
        self.percentage_complete = 0.0
        self.should_stop = False
        self.ident = ident
        self.signals = signals
        
    def get_progress(self):
        return (self.status, self.percentage_complete)
    
    def set_percentage(self, perc):
        if not 0.0 <= perc <= 100.0: raise Exception ("Incorrect Percentage of Completion")
        self.percentage_complete = perc
        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
    
    def launch_confirmed(self):
        self.status = 'Running'
        self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
        
    @inlineCallbacks
    def pause(self):
        '''
        gets called by the script to pause.
        '''
        if self.pause_lock.locked:
            self.status = 'Paused'
            self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
            self.signals.on_running_script_paused((self.ident, True))
            #call back all pause requests
            while self.pause_requests:
                request = self.pause_requests.pop()
#                print 'called back pause requests', request
                request.callback(True)
#        print 'script checking on whether should pause'
        yield self.pause_lock.acquire()
        self.pause_lock.release()
#        print 'script proceeding'
        if self.status == 'Paused':
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
        if self.pause_lock.locked:
            self.pause_lock.release()
    
    def set_pausing(self, should_pause):
        '''if asking to pause, returns a deferred which is fired when sciprt actually paused'''
        if should_pause:
            request = Deferred()
            print 'made request', request
            self.pause_requests.append(request)
            if not self.pause_lock.locked:
                #if not already paused
                self.pause_lock.acquire()#immediately returns a deferred that we don't use
                self.status = 'Pausing'
                self.signals.on_running_new_status((self.ident, self.status, self.percentage_complete))
#                print 'acquired pause', request
            else:
                print 'not acquiring because locked'
        else:
            if not self.pause_lock.locked:
                raise Exception ("Trying to unpause script that was not paused")
            request = Deferred()
            self.continue_requests.append(request)
#            print 'releasing the lock!'
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