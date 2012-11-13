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
from twisted.internet.defer import returnValue
import time
from SD_tracker_config import config as conf
from SD_calculator import double_pass, Transitions_SD, fitter
import numpy

class SDTracker(LabradServer):
    """Provides ability to track drifts of the SD line"""
    name = 'SD Tracker'
    
    onNewFit = Signal( 768120, 'signal: new fit', '' )
    
    def initServer(self):
        self.start_time = time.time()
        self.keep_measurements = conf.keep_measurements
        self.dp = double_pass()
        self.tr = Transitions_SD()
        self.fitter = fitter()
        self.t_measure = numpy.array([])
        self.B_field = numpy.array([])
        self.line_center = numpy.array([])
        self.measurements = []
        self.B_fit = None
        self.line_center_fit = None
    
    @setting(1, 'Get Transition Names', returns = '*s')
    def get_transitions(self, c):
        '''Returns the names of possible transitions'''
        return self.tr.transitions()
        
    @setting(2, 'Set Measurements', lines = '*(sv[MHz])', returns = '')
    def set_measurements(self, c, lines):
        '''takes the naames and frequencies of two lines and performs tracking'''
        t_measure = time.time() - self.start_time
        if not len(lines) == 2: raise Exception ("Please provide measurement for two lines")
        name1,f1 = lines[0]
        name2,f2 = lines[1]
        if name1 not in self.tr.transitions() or name2 not in self.tr.transitions():
            raise Exception("Lines do not match known transitions")
        if name1 == name2: raise Exception("Provided Measurements must be of different lines")
        self.measurements.append((t_measure, name1, f1))
        self.measurements.append((t_measure, name2, f2))
        f1,f2 = self.dp.reading_to_offset(f1),self.dp.reading_to_offset(f2)
        B,offset = self.tr.energies_to_magnetic_field( ( (name1,f1),(name2,f2) ))
        freq = self.dp.offset_to_reading(offset)
        self.t_measure = numpy.append(self.t_measure , t_measure)
        self.B_field = numpy.append(self.B_field , B['gauss'])
        self.line_center = numpy.append(self.line_center , freq['MHz'])
        self.do_fit()
    
    @setting(3, "Get Measurements", returns = '*(vsv[MHz])')
    def get_measurements(self, c):
        self.remove_old_measurements()
        return self.measurements
    
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
        offset = self.dp.reading_to_offset(center)
        result = self.tr.get_transition_energies(B, offset)
        for name,freq in result:
            lines.append((name, self.dp.offset_to_reading(freq)))
        return lines
    
    @setting(6, "Get Current Line", name = 's', returns = 'v[MHz]')
    def get_current_line(self, c, name):
        lines = yield self.get_current_lines(c)
        d = dict(lines)
        try:
            returnValue(d[name])
        except KeyError:
            raise Exception ("Requested line not found")
    
    @setting(7, 'Remove Measurement', point = 'i')
    def remove_measurement(self, c, point):
        '''removes the point w, can also be negative to count from the end'''
        try:
            self.t_measure = numpy.delete(self.t_measure, point)
            self.B_field = numpy.delete(self.B_field, point)
            self.line_center = numpy.delete(self.line_center, point)
            del self.measurements[2 * point]
            del self.measurements[2 * point]
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit()
    
    @setting(8, 'Get Fit History', returns = '*(v[s]v[gauss]v[MHz])')
    def get_fit_history(self, c):
        history = []
        for t,b_field,freq in zip(self.t_measure, self.B_field, self.line_center):
            history.append((WithUnit(t,'s'),WithUnit(b_field,'gauss'),WithUnit(freq, 'MHz')))
        return history
    
    @setting(9, 'History Duration', duration = 'v[s]', returns = 'v[s]')
    def get_history_duration(self, c, duration = None):
        if duration is not None:
            self.keep_measurements = duration['s']
        return WithUnit(self.keep_measurements,'s')
    
    def do_fit(self):
        self.remove_old_measurements()
        if len(self.t_measure):
            self.B_fit = self.fitter.fit(self.t_measure, self.B_field)
            self.line_center_fit = self.fitter.fit(self.t_measure, self.line_center)
        self.onNewFit(None)
    
    def remove_old_measurements(self):
        current_time = time.time() - self.start_time
        keep = numpy.where( (current_time - self.t_measure) < self.keep_measurements)
        self.t_measure = self.t_measure[keep]
        self.B_field = self.B_field[keep]
        self.line_center = self.line_center[keep]
        meas = []
        for measurement in self.measurements:
            if current_time - measurement[0] < self.keep_measurements:
                meas.append(measurement)
        self.measurements = meas

if __name__ == '__main__':
    from labrad import util
    util.runServer(SDTracker())