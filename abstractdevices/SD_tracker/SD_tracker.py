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

class SDTracker(LabradServer):
    """Provides ability to track drifts of the SD line"""
    name = 'SD Tracker'
    
    onNewFit = Signal( 768120, 'signal: new fit', '' )
    
    @inlineCallbacks
    def initServer(self):
        self.start_time = time.time()
        self.keep_line_center_measurements = conf.keep_line_center_measurements
        self.keep_B_measurements = conf.keep_B_measurements
        self.tr = Transitions_SD()
        self.fitter = fitter()
        self.t_measure_line_center = numpy.array([])
        self.t_measure_B = numpy.array([])
        self.B_field = numpy.array([])
        self.line_center = numpy.array([])
        self.B_fit = None
        self.line_center_fit = None
        self.dv = None
        yield self.connect_data_vault()
        yield self.setupListeners()
    
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
            self.line_center_dataset = yield self.dv.new(save_name, [('t', 'sec')], [('Cavity Drift','Line Center','MHz'),('Cavity Drift','B Field','gauss')])
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
    
    @setting(1, 'Get Transition Names', returns = '*s')
    def get_transitions(self, c):
        '''Returns the names of possible transitions'''
        return self.tr.transitions()
        
    @setting(2, 'Set Measurements', lines = '*(sv[MHz])', returns = '')
    def set_measurements(self, c, lines):
        '''takes the names and frequencies of two lines and performs tracking'''
        t_measure = time.time() - self.start_time
        if not len(lines) == 2: raise Exception ("Please provide measurement for two lines")
        name1,f1 = lines[0]
        name2,f2 = lines[1]
        if name1 not in self.tr.transitions() or name2 not in self.tr.transitions():
            raise Exception("Lines do not match known transitions")
        if name1 == name2: raise Exception("Provided Measurements must be of different lines")
        B,freq = self.tr.energies_to_magnetic_field( ( (name1,f1),(name2,f2) ))
        self.t_measure_B = numpy.append(self.t_measure_B , t_measure)
        self.t_measure_line_center= numpy.append(self.t_measure_line_center, t_measure)
        self.B_field = numpy.append(self.B_field , B['gauss'])
        self.line_center = numpy.append(self.line_center , freq['MHz'])
        #try to save to data vault
        yield self.save_result_datavault(t_measure, freq['MHz'], B['gauss'])
        self.do_fit()

    @setting(12, 'Set Measurement One Line', line = 'sv[MHz]', returns = '')
    def set_measurement_one_line(self, c, line):
        ''' takes name and frequency of one line, and assumes the cavity position from previous data '''
        t_measure = time.time() - self.start_time
        name,f = line
        if name not in self.tr.transitions():
            raise Exception("Line does not match a known transition")

        

    @inlineCallbacks
    def save_result_datavault(self, t_measure, freq, b_field):
        try:
            yield self.dv.add((t_measure, freq, b_field))
        except AttributeError:
            print 'Data Vault Not Available, not saving'
            yield None
    
    @setting(4, "Get Fit Parameters", name = 's', returns = '*v')
    def get_fit_parameters(self, c, name):
        '''returns the parameters for the latest fit, name can be linecenter or bfield'''
        if name == 'linecenter':
            fit = self.line_center_fit
        elif name =='bfield':
            fit = self.B_fit
        else:
            raise Exception("Provided name not found")
        if fit is not None:
            return fit
        else:
            raise Exception("Fit has not been calculated")
    
    @setting(5, "Get Current Lines", returns = '*(sv[MHz])')
    def get_current_lines(self, c):
        '''get the frequency of the current line specified by name. if name is not provided, get all lines'''
        lines = []
        current_time = time.time() - self.start_time
        try:
            B = self.fitter.evaluate(current_time, self.B_fit)
            center = self.fitter.evaluate(current_time, self.line_center_fit)
        except TypeError:
            raise Exception ("Fit is not available")
        B = WithUnit(B, 'gauss')
        center = WithUnit(center, 'MHz')
        result = self.tr.get_transition_energies(B, center)
        for name,freq in result:
            lines.append((name, freq))
        return lines
    
    @setting(6, "Get Current Line", name = 's', returns = 'v[MHz]')
    def get_current_line(self, c, name):
        lines = yield self.get_current_lines(c)
        d = dict(lines)
        try:
            returnValue(d[name])
        except KeyError:
            raise Exception ("Requested line not found")
    
    @setting(7, "Get Current B and Center", returns = '(v[MHz]v[gauss])')
    def get_current_b(self, c):
        current_time = time.time() - self.start_time
        B = self.fitter.evaluate(current_time, self.B_fit)
        center = self.fitter.evaluate(current_time, self.line_center_fit)
        B = WithUnit(B, 'gauss')
        center = WithUnit(center, 'MHz')
        returnValue((center,B))
    
    @setting(10, 'Remove B Measurement', point = 'i')
    def remove_B_measurement(self, c, point):
        '''removes the point w, can also be negative to count from the end'''
        try:
            self.t_measure_B = numpy.delete(self.t_measure_B, point)
            self.B_field = numpy.delete(self.B_field, point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit()

    @setting(11, 'Remove Line Center Measurement', point = 'i')
    def remove_line_center_measurement(self, c, point):
        '''removes the point w, can also be negative to count from the end'''
        try:
            self.t_measure_line_center = numpy.delete(self.t_measure_line_center, point)
            self.line_center = numpy.delete(self.line_center, point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit()

    @setting(8, 'Get Fit History', returns = '(*(v[s]v[gauss]) *(v[s]v[MHz]))')
    def get_fit_history(self, c):
        history_B = []
        history_line_center = []
        for t,b_field in zip(self.t_measure_B, self.B_field):
            history_B.append((WithUnit(t,'s'),WithUnit(b_field,'gauss')))
        for t, freq in zip(self.t_measure_line_center, self.line_center):
            history_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return [history_B, history_line_center]
    
    @setting(9, 'History Duration', duration = '*v[s]', returns = '*v[s]')
    def get_history_duration(self, c, duration = None):
        if duration is not None:
            self.keep_B_measurements = duration[0]['s']
            self.keep_line_center_measurements = duration[1]['s']
        return [ WithUnit(self.keep_B_measurements,'s'), WithUnit(self.keep_line_center_measurements, 's') ]
    
    def do_fit(self):
        self.remove_old_measurements()
        if (len(self.t_measure_B) and len(self.t_measure_line_center)):
            self.B_fit = self.fitter.fit(self.t_measure_B, self.B_field)
            self.line_center_fit = self.fitter.fit(self.t_measure_line_center, self.line_center)
        self.onNewFit(None)
    
    def remove_old_measurements(self):
        current_time = time.time() - self.start_time
        
        keep_line_center = numpy.where( (current_time - self.t_measure_line_center) < self.keep_line_center_measurements)
        keep_B = numpy.where( (current_time - self.t_measure_B) < self.keep_B_measurements)

        self.t_measure_line_center = self.t_measure_line_center[keep_line_center]
        self.t_measure_B = self.t_measure_B[keep_B]
        self.B_field = self.B_field[keep_B]
        self.line_center = self.line_center[keep_line_center]

if __name__ == '__main__':
    from labrad import util
    util.runServer(SDTracker())
