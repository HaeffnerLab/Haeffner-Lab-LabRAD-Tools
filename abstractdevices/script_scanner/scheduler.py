from twisted.internet.threads import deferToThread
from twisted.internet.defer import Deferred, DeferredList
from configuration import config 
from twisted.internet.task import LoopingCall
from script_status import script_semaphore

class priority_queue(object):
    '''
    priority queue with a few levels of priority
    focus on ease of use, not speed
    '''
    priorities = [0, 1]
    
    def __init__(self):
        self.d = {}
        for priority in self.priorities:
            self.d[priority] = []
    
    def put_last(self,  priority, obj):
        insert_order = 0
        for i in range(priority + 1):
            insert_order += len(self.d[i])
        self.d[priority].append(obj)
        return insert_order
    
    def put_first(self, priority, obj):
        insert_order = 0
        for i in range(priority):
            insert_order += len(self.d[i])
        self.d[priority].insert(0, obj)
        return insert_order
    
    def pop_next(self):
        next_priority = [priority for priority in self.priorities if self.d[priority]]
        return self.d[next_priority].pop()
    
    def peek_next(self):
        try:
            next_priority = [priority for priority in self.priorities if self.d[priority]][0]
            return self.d[next_priority][0]
        except ValueError:
            raise ValueError
        
    def get_all(self):
        ordered = []
        for priority in self.priorities:
            ordered.extend(self.d[priority])
        return ordered
    
    def remove_object(self, obj):
        for priority in self.priorities:
            try:
                self.d[priority].remove(obj)
                return obj
            except ValueError:
                pass 
        raise ValueError("Object not found")
        
class running_script(object):
    '''holds information about a script that is currently running'''
    def __init__(self, scan, defer_on_done, status, priority = -1, externally_launched = False):
        self.scan = scan
        self.name = scan.name
        self.status = status
        self.defer_on_done = defer_on_done
        self.priority = priority
        self.externally_launched = externally_launched

class scheduler(object):
    
    def __init__(self, signals):
        self.signals = signals
        self.running = {} #dictionary in the form identification : running_script_instance
        self.queue = priority_queue() #queue of tasks
        self._paused_by_script = []
        self.scheduled = {}
        self.scheduled_ID_counter = 0
        self.scan_ID_counter = 0
    
    def running_deferred_list(self):
        return [script.defer_on_done for script in self.running.itervalues() if not script.externally_launched]
    
    def get_running_external(self):
        return [ident for (ident, script) in self.running.iteritems() if script.externally_launched]
        
    def get_running(self):
        running = []
        for ident, script in self.running.iteritems():
            running.append((ident, script.name))
        return running
    
    def get_running_status(self, ident):
        script = self.running.get(ident, None)
        if script is None:
            return None
        else:
            return script.status
    
    def get_scheduled(self):
        scheduled = []
        for ident, (scan_name, loop) in self.scheduled.iteritems():
            scheduled.append([ident, scan_name, loop.interval])
        return scheduled
    
    def get_queue(self):
        queue = []
        for order, (ident, scan, priority) in enumerate(self.queue.get_all()):
            queue.append((ident, scan.name, order))
        return queue
    
    def remove_queued_script(self, script_ID):
        removed = False
        for ident, scan, priority in self.queue.get_all():
            if script_ID == ident: 
                removed = True
                self.queue.remove_object((script_ID, scan, priority))
                self.signals.on_queued_removed(script_ID)
        if not removed:
            raise Exception("Tring to remove scirpt ID {0} from queue but it's not in the queue".format(script_ID))
            
    def add_scan_to_queue(self, scan, priority = 'Normal'):
        #increment counter
        scan_id = self.scan_ID_counter
        self.scan_ID_counter += 1
        #add to queue
        if priority == 'Normal':
            order = self.queue.put_last(1, (scan_id, scan,  1))
        elif priority == 'First in Queue':
            order = self.queue.put_first(1, (scan_id, scan, 1))
        elif priority == 'Pause All Others':
            order = self.queue.put_last(0, (scan_id, scan, 0))
        else: 
            raise Exception ("Unrecognized priority type")
        self.signals.on_queued_new_script((scan_id, scan.name, order))
        self.launch_scripts()
        return scan_id
    
    def is_higher_priority_than_running(self, priority):
        try:
            priorities = [running.priority for running in self.running.itervalues()]
            priorities.sort()
            highest_running  =  priorities[0]
            return priority < highest_running
        except IndexError:
            return False
        
    def get_non_conflicting(self):
        '''
        returns a list of experiments that can run concurrently with currently running experiments
        '''
        non_conflicting = []
        for running, script in self.running.iteritems():
            cls_name = script.scan.script_cls.name
            non_conf = config.allowed_concurrent.get(cls_name, None)
            if non_conf is not None:
                non_conflicting.append(set(non_conf))
        if non_conflicting:
            return set.intersection(*non_conflicting)
        else:
            return set()
        return non_conflicting
    
    def add_external_scan(self, scan):
        scan_id= self.scan_ID_counter
        self.scan_ID_counter += 1
        status = script_semaphore(scan_id, self.signals)
        self.running[scan_id] = running_script(scan, Deferred(), status , externally_launched = True)
        self.signals.on_running_new_script((scan_id, scan.name))
        return scan_id
        
    def remove_from_running(self, deferred_result, running_id):
        print 'removing from running now', running_id
        del self.running[running_id]

    def remove_if_external(self, running_id):
        if running_id in self.get_running_external():
            self.remove_from_running(None, running_id)
     
    def new_scheduled_scan(self, scan, period, priority, start_now):
        '''
        @var period: in seconds
        '''
        lc = LoopingCall(self.add_scan_to_queue, scan, priority)
        new_schedule_id = self.scheduled_ID_counter
        self.scheduled[new_schedule_id] = (scan.name, lc)
        self.scheduled_ID_counter += 1
        lc.start(period, now = start_now)
        self.signals.on_scheduled_new_script((new_schedule_id, scan.name, period))
        return new_schedule_id
    
    def change_period_scheduled_script(self, scheduled_ID, period):
        try:
            name,lc = self.scheduled[scheduled_ID]
        except KeyError:
            raise Exception ("Schedule Script {0} with {1} ID does not exist".format(name, scheduled_ID))
        else:
            lc.stop()
            lc.start(period, now = False)
            self.signals.on_scheduled_new_duration((scheduled_ID, period))
    
    def cancel_scheduled_script(self, scheduled_ID):
        try:
            name, lc = self.scheduled[scheduled_ID]
        except KeyError:
            raise Exception ("Scheduled Script with ID {0} does not exist".format(scheduled_ID))
        else:
            lc.stop()
            del self.scheduled[scheduled_ID]
            self.signals.on_scheduled_removed(scheduled_ID)

    def launch_scripts(self, result = None):
        try:
            ident, scan, priority = self.queue.peek_next()
        except IndexError:
            #queue is empty
            return
        else:
            should_launch = False
            non_conflicting = self.get_non_conflicting()
            if not self.running or scan.script_cls.name in non_conflicting:
                #no running scripts or current one has no conflicts
                should_launch = True
                pause_running = False
            elif self.is_higher_priority_than_running(priority):
                should_launch = True
                pause_running = True 
        if should_launch:
            self.queue.remove_object((ident,scan, priority))
            self.signals.on_queued_removed(ident)
            self.do_launch(ident, scan, priority, pause_running)
            self.launch_scripts()
                
    def do_launch(self, ident, scan, priority, pause_running):
        d = Deferred()
        status = script_semaphore(ident, self.signals)
        self._add_to_running(ident, scan, d, status, priority)
        if pause_running:
            d.addCallback(self.pause_running, scan, ident)
        d.addCallback(self.launch_in_thread, scan, ident)
        if pause_running:
            d.addCallback(self.unpause_on_finish) 
        d.addCallback(self.remove_from_running, running_id = ident)
        d.addCallback(self.launch_scripts)
        d.callback(True)
        self.signals.on_running_new_script((ident, scan.name))
    
    def pause_running(self, result, scan, current_ident):
        paused_idents = []
        paused_deferred = []
        for ident, script in self.running.iteritems():
            non_conf = config.allowed_concurrent.get(script.name, [])
            if not scan.script_cls.name in non_conf and not script.status.status == 'Paused':
                #don't pause unless it's a conflicting experiment and it's not already paused
                if not ident == current_ident:
                    paused_idents.append(ident)
#                    print 'waiting to pause on', ident
                    d = script.status.set_pausing(True)
                    paused_deferred.append(d)
        paused_deferred = DeferredList(paused_deferred)
        self._paused_by_script = paused_idents
        return paused_deferred
    
    def unpause_on_finish(self, result):
        unpaused_defers = []
        for ident in self._paused_by_script:
            if not ident in self.running.keys():
                #if the previously paused experiment is no longer running
                self._paused_by_script.remove(ident)
                break
            if not self.running[ident].status.status == 'Running':
                #if not already running, unpause
#                print 'waiting to unfinish', ident
                d = self.running[ident].status.set_pausing(False)
                unpaused_defers.append(d)
        
        unpaused_defers = DeferredList(unpaused_defers)
        self._paused_by_script = []
        return unpaused_defers
    
    def launch_in_thread(self, result, scan, ident):
#        print 'launching now', ident
        d = deferToThread(scan.execute, ident)
        return d
    
    def _add_to_running(self, ident, scan, d, status, priority):
        self.running[ident] = running_script(scan, d, status, priority)