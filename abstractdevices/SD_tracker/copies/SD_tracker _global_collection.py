"""
### BEGIN NODE INFO
[info]
name = SD Tracker
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
from labrad.server import setting, LabradServer, Signal
from labrad.units import WithUnit
from twisted.internet.defer import returnValue, inlineCallbacks
import time
from SD_tracker_config import config as conf
from SD_calculator import Transitions_SD, fitter
import numpy
#from labrad.units import WithUnit

SIGNALID_lattice = 62405

class SDTracker(LabradServer):
    """Provides ability to track drifts of the SD line"""
    name = 'SD Tracker'
    
    onNewFit = Signal( 768120, 'signal: new fit', '' )
    
    @inlineCallbacks
    def initServer(self):
        self.start_time = time.time()
        self.keep_line_center_measurements = conf.keep_line_center_measurements
        self.fitter = fitter()
        self.t_measure_line_center = numpy.array([])     
        self.t_measure_line_center_nofit = numpy.array([])
        self.line_center_nofit = numpy.array([])                
        self.line_center = numpy.array([])
        self.line_center_fit = None
        self.dv = None
        yield self.connect_data_vault()
        yield self.connect_sd_tracker1()
        yield self.setupListeners()
    
    @inlineCallbacks
    def connect_sd_tracker1(self):
        try:
            from labrad.wrappers import connectAsync
            self.cxn1 = yield connectAsync('192.168.169.197', password = 'lab', tls_mode = 'off')
            self.server1 = self.cxn1.sd_tracker
            yield self.server1.signal__new_fit(SIGNALID_lattice)
            yield self.server1.addListener(listener = self.grab_data_server1, source = None, ID = SIGNALID_lattice)
        except:
            print 'cannot connect to local SD Tracker 197'

    @inlineCallbacks
    def grab_data_server1(self,x,y):
        t_measure = time.time() - self.start_time
        last_line_center = yield self.server1.get_last_line_center()
        self.line_center = numpy.append(self.line_center, last_line_center)
        self.t_measure_line_center = numpy.append(self.t_measure_line_center, t_measure)
        self.do_fit()

    @inlineCallbacks
    def connect_data_vault(self):
        try:
            #reconnect to data vault and navigate to the directory
            self.dv = yield self.client.data_vault
            directory = list(conf.save_folder)
            localtime = time.localtime()
            dirappend = [time.strftime("%Y%b%d",localtime)]
            directory.extend(dirappend)
            yield self.dv.cd(directory, True)
            datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
            save_name = '{0} {1}'.format(conf.dataset_name, datasetNameAppend)
            self.line_center_dataset = yield self.dv.new(save_name, [('t', 'sec')], [('Cavity Drift','Line Center','MHz')])
            yield self.dv.add_parameter('start_time', time.time())
        except AttributeError:
            self.dv = None
        
    @inlineCallbacks
    def setupListeners(self):
        yield self.client.manager.subscribe_to_named_message('Server Connect', conf.signal_id, True)
        yield self.client.manager.subscribe_to_named_message('Server Disconnect', conf.signal_id+1, True)
        yield self.client.manager.addListener(listener = self.followServerConnect, source = None, ID = conf.signal_id)
        yield self.client.manager.addListener(listener = self.followServerDisconnect, source = None, ID = conf.signal_id+1)
    
    @inlineCallbacks
    def followServerConnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Data Vault':
            yield self.connect_data_vault()
        else:
            yield None
    
    @inlineCallbacks
    def followServerDisconnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Data Vault':
            self.dv = None
        yield None

    @inlineCallbacks
    def save_result_datavault(self, t_measure, freq):
        try:
            yield self.dv.add((t_measure, freq))
        except AttributeError:
            print 'Data Vault Not Available, not saving'
            yield None
    
    @setting(1, "Get Fit Parameters", returns = '*v')
    def get_fit_parameters(self, c):
        '''returns the parameters for the latest fit'''
        fit = self.line_center_fit
        if fit is not None:
            return fit
        else:
            raise Exception("Fit has not been calculated")
        
    @setting(5, "Get Current Center", returns = 'v[MHz]')
    def get_current_center(self, c):
        current_time = time.time() - self.start_time
        center = self.fitter.evaluate(current_time, self.line_center_fit)
        center = WithUnit(center, 'MHz')
        return center
        #returnValue(center)

    @setting(4, 'Remove Line Center Measurement', point = 'i')
    def remove_line_center_measurement(self, c, point):
        '''removes the point w, can also be negative to count from the end'''
        try:
            self.t_measure_line_center_nofit = numpy.append(self.t_measure_line_center_nofit, self.t_measure_line_center[point])
            self.line_center_nofit = numpy.append(self.line_center_nofit, self.line_center[point])
            self.t_measure_line_center = numpy.delete(self.t_measure_line_center, point)
            self.line_center = numpy.delete(self.line_center, point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit()

    @setting(2, 'Get Fit History', returns = '*(v[s]v[MHz])')
    def get_fit_history(self, c):
        history_line_center = []
        for t, freq in zip(self.t_measure_line_center, self.line_center):
            history_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return history_line_center
    
    @setting(6, 'Get Excluded Points', returns = '*(v[s]v[MHz])')
    def get_excluded_points(self, c):
        excluded_line_center = []
        for t, freq in zip(self.t_measure_line_center_nofit, self.line_center_nofit):
            excluded_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return excluded_line_center
    
    @setting(3, 'History Duration', duration = 'v[s]', returns = 'v[s]')
    def get_history_duration(self, c, duration = None):
        if duration is not None:
            self.keep_line_center_measurements = duration['s']
            self.do_fit()
        return WithUnit(self.keep_line_center_measurements, 's')

    @setting(7, 'Get Last Line Center', returns = 'v')
    def get_last_line_center(self, c):
        ''' returns the last entered line center '''
        return self.line_center[-1]

    @setting(8, 'Get Line Center', returns = '*v')
    def get_line_center(self, c):
        ''' returns all entered line centers '''
        return self.line_center

    @setting(15, 'Set Measurements with Line Center', freq = 'v[MHz]', returns = '')
    def set_measurements_with_line_center(self, c, freq):
        '''takes the line center and sets up tracking'''
        t_measure = time.time() - self.start_time

        # arrays which contain the time when the measurement was taken
        self.t_measure_line_center= numpy.append(self.t_measure_line_center, t_measure)

        # arrays of line center
        self.line_center = numpy.append(self.line_center , freq['MHz'])
        
        # try to save to data vault
        # yield self.save_result_datavault(t_measure, freq['MHz'])
        # save the epoch time, NOT the time since the software started t_measure
        yield self.save_result_datavault(time.time(), freq['MHz'])
        self.do_fit()

    def do_fit(self):
        self.remove_old_measurements()
        if len(self.t_measure_line_center):
            self.line_center_fit = self.fitter.fit(self.t_measure_line_center, self.line_center)
        self.onNewFit(None)
    
    def remove_old_measurements(self):
        current_time = time.time() - self.start_time
        
        keep_line_center = numpy.where( (current_time - self.t_measure_line_center) < self.keep_line_center_measurements)

        self.t_measure_line_center = self.t_measure_line_center[keep_line_center]
        self.line_center = self.line_center[keep_line_center]

if __name__ == '__main__':
    from labrad import util
    util.runServer(SDTracker())
