from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from helper_widgets.helper_widgets import saved_frequencies_table
from helper_widgets.compound_widgets import table_dropdowns_with_entry
import numpy
from drift_tracker_config import config_729_tracker as c

'''
Drift Tracker GUI. 
Version 1.1
'''

class drift_tracker(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.cxn = cxn
        self.subscribed = False
        #see if favoirtes are provided in the configuration. if not, use an empty dictionary
        try:
            self.favorites =  c.favorites
        except AttributeError:
            self.favorites = {}
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
        self.entry_table = table_dropdowns_with_entry(self.reactor, limits = c.frequency_limit, suffix = ' MHz', sig_figs = 4, favorites = self.favorites)
        self.entry_button = QtGui.QPushButton("Submit")
        self.remove_button = QtGui.QPushButton("Remove")
        self.remove_count = QtGui.QSpinBox()
        self.remove_count.setRange(-20,20)
        self.track_duration = QtGui.QSpinBox()
        self.track_duration.setKeyboardTracking(False)
        self.track_duration.setSuffix('min')
        self.track_duration.setRange(1, 1000)
        layout.addWidget(self.frequency_table, 0, 0, 1, 1)
        layout.addWidget(self.entry_table, 0, 1 , 1 , 1)
        layout.addWidget(self.entry_button, 1, 1, 1, 1)
        remove_layout = QtGui.QHBoxLayout() 
        remove_layout.addWidget(self.remove_count)
        remove_layout.addWidget(self.remove_button)    
        update_layout = QtGui.QHBoxLayout()
        keep_layout = QtGui.QHBoxLayout()
        keep_layout.addWidget(QtGui.QLabel("Tracking Duration"))
        keep_layout.addWidget(self.track_duration)
        layout.addLayout(update_layout, 2, 1, 1, 1)
        layout.addLayout(remove_layout, 1, 0, 1, 1)
        layout.addLayout(keep_layout, 3, 1, 1, 1)
        return layout
        
    def connect_layout(self):
        self.remove_button.clicked.connect(self.on_remove)
        self.entry_button.clicked.connect(self.on_entry)
        self.track_duration.valueChanged.connect(self.on_new_track_duration)
    
    @inlineCallbacks
    def initialize_layout(self):
        server = self.cxn.servers['SD Tracker']
        transitions = yield server.get_transition_names()
        self.entry_table.fill_out(transitions)
        duration = yield server.history_duration()
        self.track_duration.blockSignals(True)
        self.track_duration.setValue(duration['min'])
        self.track_duration.blockSignals(False)
        yield self.on_new_fit(None, None)
    
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
    def on_remove(self, clicked):
        to_remove = self.remove_count.value()
        server = self.cxn.servers['SD Tracker']
        try:
            yield server.remove_measurement(to_remove)
        except self.Error as e:
            self.displayError(e.msg)
    
    @inlineCallbacks
    def on_entry(self, clicked):
        server = self.cxn.servers['SD Tracker']
        info = self.entry_table.get_info()
        with_units = [(name, self.WithUnit(val, 'MHz')) for name,val in info]
        try:
            yield server.set_measurements(with_units)
        except self.Error as e:
            self.displayError(e.msg)
    
    @inlineCallbacks
    def on_new_track_duration(self, value):
        server = self.cxn.servers['SD Tracker']
        rate = self.WithUnit(value, 'min')
        yield server.history_duration(rate)
        
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
        self.cxn.on_connect['SD Tracker'].append( self.reinitialize_tracker)
        self.cxn.on_disconnect['SD Tracker'].append( self.disable)
        self.connect_layout()
        
    @inlineCallbacks
    def subscribe_tracker(self):
        yield self.cxn.servers['SD Tracker'].signal__new_fit(c.ID, context = self.context)
        yield self.cxn.servers['SD Tracker'].addListener(listener = self.on_new_fit, source = None, ID = c.ID, context = self.context)
        yield self.initialize_layout()
        self.subscribed = True
    
    @inlineCallbacks
    def reinitialize_tracker(self):
        self.setDisabled(False)
        yield self.cxn.servers['SD Tracker'].signal__new_fit(c.ID, context = self.context)
        if not self.subscribed:
            yield self.cxn.servers['SD Tracker'].addListener(listener = self.on_new_fit, source = None, ID = c.ID, context = self.context)
            yield self.initialize_layout()
            self.subscribed = True
    
    @inlineCallbacks
    def on_new_fit(self, x, y):
        yield self.update_lines()
        yield self.update_fit()
    
    @inlineCallbacks
    def update_fit(self):
        try:
            server = self.cxn.servers['SD Tracker']
            history = yield server.get_fit_history()
            fit_b = yield server.get_fit_parameters('bfield')
            fit_f = yield server.get_fit_parameters('linecenter')
        except Exception as e:
            #no fit available
            pass
        else:
            inunits_b = [(t['min'], b['mgauss']) for (t,b,freq) in history]
            inunits_f = [(t['min'], freq['kHz']) for (t,b,freq) in history]
            self.update_track(inunits_b, self.b_drift, self.b_drift_lines)
            self.update_track(inunits_f, self.line_drift, self.line_drift_lines)
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
            server = self.cxn.servers['SD Tracker']
            lines = yield server.get_current_lines()
        except Exception as e:
            #no lines available
            returnValue(None)
        else:
            self.update_spectrum(lines)
            self.update_listing(lines)
            returnValue(lines)
    
    def update_track(self, meas, axes, lines):
        #clear all current lines
        for i in range(len(lines)):
            line = lines.pop()
            line.remove()
        x = numpy.array([m[0] for m in meas])
        y = [m[1] for m in meas]
        #annotate the last point
        try:
            last = y[-1]
        except IndexError:
            pass
        else:
            label = axes.annotate('Last Point: {0:.2f} {1}'.format(last, axes.get_ylabel()), xy = (0.5, 0.9), xycoords = 'axes fraction', fontsize = 13.0)
            lines.append(label)
        line = axes.plot(x,y, 'b*')[0]
        lines.append(line)
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

    def update_listing(self, lines):
        listing = [(self.favorites.get(line, line), freq) for line,freq in lines]
        self.frequency_table.fill_out_widget(listing)
        
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
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = drift_tracker(reactor)
    widget.show()
    reactor.run()