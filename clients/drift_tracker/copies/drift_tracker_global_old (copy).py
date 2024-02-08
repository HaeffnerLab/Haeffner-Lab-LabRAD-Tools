from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

# this try and except avoids the error "RuntimeError: wrapped C/C++ object of type QWidget has been deleted"
try:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
except:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from helper_widgets.helper_widgets import saved_frequencies_table
from helper_widgets.compound_widgets import table_dropdowns_with_entry
import numpy
import time
from drift_tracker_config import config_729_tracker as c

'''
Drift Tracker GUI. 
Version 1.15
'''

class drift_tracker(QtGui.QWidget):
    def __init__(self, reactor, clipboard = None, cxn = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.clipboard = clipboard
        self.cxn = cxn
        self.subscribed = False
        #see if favorites are provided in the configuration. if not, use an empty dictionary
        try:
            self.favorites =  c.favorites
        except AttributeError:
            self.favorites = {}
        try:
            self.initial_selection =  c.initial_selection
        except AttributeError:
            self.initial_selection = []
        try:
            self.initial_values =  c.initial_values
        except AttributeError:
            self.initial_values = []

        updater = LoopingCall(self.update_lines)
        updater.start(c.update_rate)
        self.create_layout()
        self.connect_labrad()
    
    def create_layout(self):
        layout = QtGui.QGridLayout()
        plot_layout = self.create_drift_layout()
        widget_layout = self.create_widget_layout()
        spectrum_layout = self.create_spectrum_layout()
        layout.addLayout(plot_layout, 0, 0, 1, 2)
        layout.addLayout(widget_layout, 1, 0, 1, 1)
        layout.addLayout(spectrum_layout, 1, 1, 1, 1)
        self.setLayout(layout)
   
    def create_drift_layout(self):
        layout = QtGui.QVBoxLayout()
        self.fig = Figure()
        self.drift_canvas = FigureCanvas(self.fig)
        self.drift_canvas.setParent(self)  
        gs = gridspec.GridSpec(1, 2, wspace=0.15, left = 0.05, right = 0.95)
        line_drift = self.fig.add_subplot(gs[0, 0])
        line_drift.set_xlabel('Time (min)')
        line_drift.set_ylabel('KHz')
        line_drift.set_title("Line Center Drift")
        self.line_drift = line_drift
        self.line_drift_lines = []
        self.line_drift_fit_line = []
        b_drift = self.fig.add_subplot(gs[0, 1], sharex=line_drift)
        b_drift.set_xlabel('Time (min)')
        b_drift.set_ylabel('mgauss')
        b_drift.set_title("B Field Drift")
        self.b_drift_twin = b_drift.twinx()
        self.b_drift_twin.set_ylabel('Effective Frequency (kHz)')
        self.b_drift_twin_lines = []
        self.b_drift_lines = []
        self.b_drift_fit_line = []
        self.b_drift = b_drift
        self.mpl_toolbar = NavigationToolbar(self.drift_canvas, self)
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.drift_canvas)
        return layout
    
    def create_spectrum_layout(self):
        layout = QtGui.QVBoxLayout()
        self.fig = Figure()
        self.spec_canvas = FigureCanvas(self.fig)
        self.spec_canvas.setParent(self)  
        gs = gridspec.GridSpec(1, 1, wspace=0.15, left = 0.05, right = 0.95)
        spec = self.fig.add_subplot(gs[0, 0])
        spec.set_xlim(left = c.frequency_limit[0], right = c.frequency_limit[1])
        spec.set_ylim(bottom = 0, top = 1)
        spec.set_xlabel('MHz')
        spec.set_ylabel('Arb')
        spec.set_title("Predicted Spectrum")
        self.spec = spec
        self.mpl_toolbar = NavigationToolbar(self.spec_canvas, self)
        self.spectral_lines = []
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.spec_canvas)
        return layout
    
    def create_widget_layout(self):
        layout = QtGui.QGridLayout()
        self.frequency_table = saved_frequencies_table(self.reactor, suffix = ' MHz', sig_figs = 4)
        self.entry_table = table_dropdowns_with_entry(self.reactor, limits = c.frequency_limit, suffix = ' MHz', sig_figs = 4, favorites = self.favorites, initial_selection = self.initial_selection, initial_values = self.initial_values)
        
        self.Bfield_entry = QtGui.QDoubleSpinBox()
        self.Bfield_entry.setRange(0.0, 10000.0)
        self.Bfield_entry.setDecimals(6)
        self.Bfield_entry.setSuffix(' mGauss')

        self.linecenter_entry = QtGui.QDoubleSpinBox()
        self.linecenter_entry.setRange(-50000.0, 0.0)
        self.linecenter_entry.setDecimals(6)
        self.linecenter_entry.setSuffix(' kHz')
        
        self.entry_Bfield_and_center_button = QtGui.QPushButton("Submit B and Line Center")

        self.entry_button = QtGui.QPushButton("Submit Lines")
        self.copy_clipboard_button = QtGui.QPushButton("Copy Info to Clipboard")

        self.remove_all_B_and_lines_button = QtGui.QPushButton("Remove all B and Line Centers")
        #self.remove_all_B_and_lines_button.setDisabled(True) # not programmed yet

        self.remove_B_button = QtGui.QPushButton("Remove B")
        self.remove_line_center_button = QtGui.QPushButton("Remove Line Center")

        self.remove_B_count = QtGui.QSpinBox()
        self.remove_B_count.setRange(-20,20)
        self.remove_line_center_count = QtGui.QSpinBox()
        self.remove_line_center_count.setRange(-20,20)
        
        self.track_B_duration = QtGui.QSpinBox()
        self.track_B_duration.setKeyboardTracking(False)
        self.track_B_duration.setSuffix('min')
        self.track_B_duration.setRange(1, 1000)
        
        self.track_line_center_duration = QtGui.QSpinBox()
        self.track_line_center_duration.setKeyboardTracking(False)
        self.track_line_center_duration.setSuffix('min')
        self.track_line_center_duration.setRange(1, 1000)
        
        layout.addWidget(self.frequency_table, 0, 0, 6, 1)
        layout.addWidget(self.entry_table, 0, 1, 2, 1)
        layout.addWidget(self.entry_button, 2, 1, 1, 1)
        layout.addWidget(self.Bfield_entry, 3, 1, 1, 1)
        layout.addWidget(self.linecenter_entry, 4, 1, 1, 1)
        layout.addWidget(self.entry_Bfield_and_center_button, 5, 1, 1, 1)

        hlp_layout = QtGui.QHBoxLayout()
        hlp_layout.addWidget(self.copy_clipboard_button)
        hlp_layout.addWidget(self.remove_all_B_and_lines_button)
        
        remove_B_layout = QtGui.QHBoxLayout() 
        remove_B_layout.addWidget(self.remove_B_count)
        remove_B_layout.addWidget(self.remove_B_button)    

        remove_line_center_layout = QtGui.QHBoxLayout() 
        remove_line_center_layout.addWidget(self.remove_line_center_count)
        remove_line_center_layout.addWidget(self.remove_line_center_button)    

        keep_B_layout = QtGui.QHBoxLayout()
        keep_B_layout.addWidget(QtGui.QLabel("Tracking Duration (B)"))
        keep_B_layout.addWidget(self.track_B_duration)

        keep_line_center_layout = QtGui.QHBoxLayout()
        keep_line_center_layout.addWidget(QtGui.QLabel("Tracking Duration (Line Center)"))
        keep_line_center_layout.addWidget(self.track_line_center_duration)
        
        layout.addLayout(hlp_layout, 6, 0, 1, 1)
        layout.addLayout(remove_B_layout, 7, 0, 1, 1)
        layout.addLayout(remove_line_center_layout, 8, 0, 1, 1)
        layout.addLayout(keep_B_layout, 7, 1, 1, 1)
        layout.addLayout(keep_line_center_layout, 8, 1, 1, 1)
        
        return layout
        
    def connect_layout(self):
        self.remove_B_button.clicked.connect(self.on_remove_B)
        self.remove_line_center_button.clicked.connect(self.on_remove_line_center)
        self.remove_all_B_and_lines_button.clicked.connect(self.on_remove_all_B_and_line_centers)
        
        self.entry_button.clicked.connect(self.on_entry)
        self.entry_Bfield_and_center_button.clicked.connect(self.on_entry_Bfield_and_center)
        
        self.track_B_duration.valueChanged.connect(self.on_new_B_track_duration)
        self.track_line_center_duration.valueChanged.connect(self.on_new_line_center_track_duration)
        self.copy_clipboard_button.pressed.connect(self.do_copy_info_to_clipboard)
    
    @inlineCallbacks
    def initialize_layout(self):
        server = yield self.cxn.get_server('SD Tracker')
        transitions = yield server.get_transition_names()
        self.entry_table.fill_out(transitions)
        duration_B, duration_line_center = yield server.history_duration()
        self.track_B_duration.blockSignals(True)
        self.track_line_center_duration.blockSignals(True)
        self.track_B_duration.setValue(duration_B['min'])
        self.track_line_center_duration.setValue(duration_line_center['min'])
        self.track_B_duration.blockSignals(False)
        self.track_line_center_duration.blockSignals(False)
        yield self.on_new_fit(None, None)
    
    @inlineCallbacks
    def do_copy_info_to_clipboard(self):
        try:
            server = yield self.cxn.get_server('SD Tracker')
            lines = yield server.get_current_lines()
            b_history, center_history =  yield server.get_fit_history()
            b_value =  b_history[-1][1]
            center_value = center_history[-1][1]
        except Exception as e:
            #no lines available
            pass
        else:
            date = time.strftime('%m/%d/%Y')
            d = dict(lines)
            text = '| {0} || {1:.4f} MHz || {2:.4f} MHz || {3:.4f} MHz || {4:.4f} MHz || {5:.4f} G || comment'.format(date, d['S+1/2D-3/2']['MHz'], d['S-1/2D-5/2']['MHz'], d['S-1/2D-1/2']['MHz'], center_value['MHz'], b_value['gauss'])
            if self.clipboard is not None:
                self.clipboard.setText(text)
    
    def on_update_enable(self, enable):
        rate = self.update_rate.value()
        if enable:
            self.updater.start(rate, now = True)
        else:
            self.updater.stop()
    
    def on_update_rate_change(self, rate):
        if self.updater.running:
            self.updater.stop()
            self.updater.start(rate, now = True)
            
    @inlineCallbacks
    def on_remove_B(self, clicked):
        to_remove = self.remove_B_count.value()
        server = yield self.cxn.get_server('SD Tracker')
        try:
            yield server.remove_b_measurement(to_remove)
            #print to_remove
        except self.Error as e:
            self.displayError(e.msg)

    @inlineCallbacks
    def on_remove_line_center(self, clicked):
        to_remove = self.remove_line_center_count.value()
        server = yield self.cxn.get_server('SD Tracker')
        try:
            yield server.remove_line_center_measurement(to_remove)
        except self.Error as e:
            self.displayError(e.msg)

    @inlineCallbacks
    def on_remove_all_B_and_line_centers(self, clicked):
        server = yield self.cxn.get_server('SD Tracker')

        b_field = yield server.get_b_field()
        line_center = yield server.get_line_center()

        # remove all line centers
        try:
            # call the remove function as many times as the array is long
            for k in range(len(line_center)):
                yield server.remove_line_center_measurement(0)
        except self.Error as e:
            self.displayError(e.msg)

        # remove all Bfields
        try:
            # call the remove function as many times as the array is long
            for k in range(len(b_field)):
                yield server.remove_b_measurement(0)
        except self.Error as e:
            self.displayError(e.msg)

    @inlineCallbacks
    def on_entry(self, clicked):
        server = yield self.cxn.get_server('SD Tracker')
        info = self.entry_table.get_info()
        with_units = [(name, self.WithUnit(val, 'MHz')) for name,val in info]
        try:
            yield server.set_measurements(with_units)

            # update entry boxes with the last points
            b_field = yield server.get_last_b_field()
            line_center = yield server.get_last_line_center()

            self.Bfield_entry.setValue(b_field*1.0e3)
            self.linecenter_entry.setValue(line_center*1.0e3)

            self.resize_spec_graph()

        except self.Error as e:
            self.displayError(e.msg)
    
    @inlineCallbacks
    def on_entry_Bfield_and_center(self, clicked):
        server = yield self.cxn.get_server('SD Tracker')
        B_with_units = self.WithUnit(self.Bfield_entry.value()/1.0e3, 'gauss')
        f_with_units = self.WithUnit(self.linecenter_entry.value()/1.0e3, 'MHz')

        hlp1 = [('Bfield', B_with_units)]
        hlp2 = [('line_center', f_with_units)] # workaround, needs fixing

        try:
            yield server.set_measurements_with_bfield_and_line_center(hlp1, hlp2)

            # get the currently chosen lines
            hlp = yield server.get_lines_from_bfield_and_center(B_with_units, f_with_units)
            hlp = dict(hlp)

            line_info = self.entry_table.get_info() # e.g. [('S-1/2D-3/2', -14.3), ('S-1/2D-5/2', -19.3)]
            for k in range(len(line_info)):
                # get the current line from the server
                new_freq = hlp[line_info[k][0]]
                self.entry_table.cellWidget(k, 1).setValue(new_freq.value)                

            self.resize_spec_graph()

        except self.Error as e:
            self.displayError(e.msg)        

    @inlineCallbacks
    def on_new_B_track_duration(self, value):
        server = yield self.cxn.get_server('SD Tracker')
        rate_B = self.WithUnit(value, 'min')
        rate_line_center = self.WithUnit(self.track_line_center_duration.value(), 'min')
        yield server.history_duration((rate_B, rate_line_center))
    
    @inlineCallbacks
    def on_new_line_center_track_duration(self, value):
        server = yield self.cxn.get_server('SD Tracker')
        rate_line_center = self.WithUnit(value, 'min')
        rate_B = self.WithUnit(self.track_B_duration.value(), 'min')
        yield server.history_duration((rate_B, rate_line_center))
        
    @inlineCallbacks
    def connect_labrad(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        if self.cxn is None:
            from common.clients.connection import connection
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.subscribe_tracker()
        except Exception as e:
            self.setDisabled(True)
        self.cxn.add_on_connect('SD Tracker', self.reinitialize_tracker)
        self.cxn.add_on_disconnect('SD Tracker', self.disable)

        from labrad.wrappers import connectAsync
        self.cxn1 = yield connectAsync('192.168.169.197', password = 'lab', tls_mode = 'off')
        self.server1 = self.cxn1.sd_tracker
        yield self.server1.signal__new_fit(62405)
        yield self.server1.addListener(listener = self.grab_data_server1, source = None, ID = 62405)
        
        self.connect_layout()
        
    @inlineCallbacks
    def subscribe_tracker(self):
        server = yield self.cxn.get_server('SD Tracker')
        yield server.signal__new_fit(c.ID, context = self.context)
        yield server.addListener(listener = self.on_new_fit, source = None, ID = c.ID, context = self.context)
        yield self.initialize_layout()
        self.subscribed = True
    
    @inlineCallbacks
    def reinitialize_tracker(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('SD Tracker')
        yield server.signal__new_fit(c.ID, context = self.context)
        if not self.subscribed:
            yield server.addListener(listener = self.on_new_fit, source = None, ID = c.ID, context = self.context)
            yield self.initialize_layout()
            self.subscribed = True
    
    @inlineCallbacks
    def on_new_fit(self, x, y):
        yield self.update_lines()
        yield self.update_fit()
    
    @inlineCallbacks
    def update_fit(self):
        try:
            server = yield self.cxn.get_server('SD Tracker')
            history_B, history_line_center = yield server.get_fit_history()
            excluded_B, excluded_line_center = yield server.get_excluded_points()
            fit_b = yield server.get_fit_parameters('bfield')
            fit_f = yield server.get_fit_parameters('linecenter')
        except Exception as e:
            #no fit available
            print(e)
            pass
        else:
            inunits_b = [(t['min'], b['mgauss']) for (t,b) in history_B]
            inunits_f = [(t['min'], freq['kHz']) for (t,freq) in history_line_center]
            inunits_b_nofit = [(t['min'], b['mgauss']) for (t,b) in excluded_B]
            inunits_f_nofit = [(t['min'], freq['kHz']) for (t,freq) in excluded_line_center]            
            self.update_track((inunits_b,inunits_b_nofit), self.b_drift, self.b_drift_lines)
            self.update_track((inunits_f,inunits_f_nofit), self.line_drift, self.line_drift_lines)

            self.plot_fit_b(fit_b)
            self.plot_fit_f(fit_f)
            
    def plot_fit_b(self, p):
        for i in range(len(self.b_drift_fit_line)):
            l = self.b_drift_fit_line.pop()
            l.remove()
        for i in range(len(self.b_drift_twin_lines)):
            l = self.b_drift_twin_lines.pop()
            l.remove()
        xmin,xmax = self.b_drift.get_xlim()
        xmin-= 10
        xmax+= 10
        
        points = 1000        
        x = numpy.linspace(xmin, xmax, points) 
        y = 1000 * numpy.polyval(p, 60*x)
        frequency_scale = 1.4 #KHz / mgauss
        l = self.b_drift.plot(x, y, '-r')[0]
        twin = self.b_drift_twin.plot(x, frequency_scale * y, alpha = 0)[0]
        self.b_drift_twin_lines.append(twin)
        label = self.b_drift.annotate('Slope {0:.1f} microgauss/sec'.format(10**6 * p[-2]), xy = (0.5, 0.8), xycoords = 'axes fraction', fontsize = 13.0)
        self.b_drift_fit_line.append(label)
        self.b_drift_fit_line.append(l)
        self.drift_canvas.draw()
    
    def plot_fit_f(self, p):
        for i in range(len(self.line_drift_fit_line)):
            l = self.line_drift_fit_line.pop()
            l.remove()
        xmin,xmax = self.b_drift.get_xlim()
        xmin-= 10
        xmax+= 10
        points = 1000
        x = numpy.linspace(xmin, xmax, points) 
        y = 1000 * numpy.polyval(p, 60*x)
        l = self.line_drift.plot(x, y, '-r')[0]
        label = self.line_drift.annotate('Slope {0:.1f} Hz/sec'.format(10**6 * p[-2]), xy = (0.5, 0.8), xycoords = 'axes fraction', fontsize = 13.0)
        self.line_drift_fit_line.append(l)
        self.line_drift_fit_line.append(label)
        self.drift_canvas.draw()
    
    @inlineCallbacks
    def update_lines(self):
        try:
            server = yield self.cxn.get_server('SD Tracker')
            lines = yield server.get_current_lines()
        except Exception as e:
            #no lines available
            returnValue(None)
        else:
            self.update_spectrum(lines)
            self.update_listing(lines)
            returnValue(lines)
    
    def update_track(self, meas, axes, lines):
        # clear all current lines
        for i in range(len(lines)):
            line = lines.pop()
            line.remove()
        fitted = meas[0]
        not_fitted = meas[1]
        x = numpy.array([m[0] for m in fitted])
        y = [m[1] for m in fitted]
        xnofit = numpy.array([m[0] for m in not_fitted])
        ynofit = [m[1] for m in not_fitted]
        
        # annotate the last point
        try:
            last = y[-1]
        except IndexError:
            pass
        else:
            label = axes.annotate('Last Point: {0:.2f} {1}'.format(last, axes.get_ylabel()), xy = (0.5, 0.9), xycoords = 'axes fraction', fontsize = 13.0)
            lines.append(label)
        line = axes.plot(x,y, 'b*')[0]
        line_nofit = axes.plot(xnofit,ynofit, 'ro')[0]
        
        lines.append(line)
        lines.append(line_nofit)
        
        #set window limits
        xmin = numpy.amin(x)
        xmax = numpy.amax(x)
        ymin = numpy.amin(y)
        ymax = numpy.amax(y)
        if xmin == xmax:
            xlims = [xmin-5,xmax+5]
            ylims = [ymin-2,ymax+2]
        else:
            xspan = xmax-xmin
            yspan = ymax-ymin
            xlims = [xmin-0.25*xspan,xmax+0.5*xspan]
            ylims = [ymin-0.5*yspan,ymax+0.5*yspan]
        axes.set_xlim(xlims)
        axes.set_ylim(ylims)
        
        self.drift_canvas.draw()
               
    def update_spectrum(self, lines):
        #clear all lines by removing them from the self.spectral_lines list
        for i in range(len(self.spectral_lines)):
            line = self.spectral_lines.pop()
            line.remove()
        #sort by frequency to add them in the right order
        srt = sorted(lines, key = lambda x: x[1])
        num = len(srt)
        for i, (linename, freq) in enumerate(srt):
            line = self.spec.axvline(freq['MHz'], linewidth=1.0, ymin = 0, ymax = 1)
            self.spectral_lines.append(line)
            #check to see if linename in the favorites dictionary, if not use the linename for display
            display_name = self.favorites.get(linename, linename)
            label = self.spec.annotate(display_name, xy = (freq['MHz'], 0.9 - i * 0.7 / num), xycoords = 'data', fontsize = 13.0)
            self.spectral_lines.append(label)
        self.spec_canvas.draw()

    def update_listing(self, lines): ##########################33
        listing = [(self.favorites.get(line, line), freq) for line,freq in lines]
        zeeman = self.calc_zeeman(listing)
        listing.append(zeeman)
        self.frequency_table.fill_out_widget(listing)
        
    def calc_zeeman(self, listing):
        line1 = 'S+1/2D+1/2'
        line2 = 'S-1/2D+1/2'
        for line,freq in listing:
            if line == line1:
                freq1 = freq['MHz']
            if line == line2:
                freq2 = freq['MHz']
        zeeman = ('Zeeman Splitting',self.WithUnit(-freq1+freq2, 'MHz'))
        return zeeman
    
    @inlineCallbacks
    def resize_spec_graph(self):
        # set the limits of the predicted spectrum to the extrema
        try:
            server = yield self.cxn.get_server('SD Tracker')
            curr_lines = yield server.get_current_lines()

            curr_lines = dict(curr_lines)
            hlp, my_min = min(curr_lines.iteritems(), key = lambda x: x[1])
            hlp, my_max = max(curr_lines.iteritems(), key = lambda x: x[1])
            self.spec.set_xlim(left = my_min.value - 1.0, right = my_max.value + 1.0)

        except Exception as e:
            #no lines available
            return
        
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
        
    def displayError(self, text):
        #runs the message box in a non-blocking method
        message = QtGui.QMessageBox(self)
        message.setText(text)
        message.open()
        message.show()
        message.raise_()
    
    def closeEvent(self, x):
        self.reactor.stop()  

    @inlineCallbacks
    def grab_data_server1(self,x,y):
        server = yield self.cxn.get_server('SD Tracker')

        last_line_center = yield self.server1.get_last_line_center()
        last_b_field = yield self.server1.get_last_b_field()
        B_with_units = self.WithUnit(last_b_field, 'gauss')
        f_with_units = self.WithUnit(last_line_center, 'MHz')

        hlp1 = [('Bfield', B_with_units)]
        hlp2 = [('line_center', f_with_units)]

        try:
            yield server.set_measurements_with_bfield_and_line_center(hlp1, hlp2)

            # get the currently chosen lines
            hlp = yield server.get_lines_from_bfield_and_center(B_with_units, f_with_units)
            hlp = dict(hlp)

            line_info = self.entry_table.get_info() # e.g. [('S-1/2D-3/2', -14.3), ('S-1/2D-5/2', -19.3)]
            for k in range(len(line_info)):
                # get the current line from the server
                new_freq = hlp[line_info[k][0]]
                self.entry_table.cellWidget(k, 1).setValue(new_freq.value)                

            self.resize_spec_graph()

        except self.Error as e:
            self.displayError(e.msg)

    
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    clipboard = a.clipboard()
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = drift_tracker(reactor, clipboard)
    widget.show()
    reactor.run()
