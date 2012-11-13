from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from helper_widgets import saved_frequencies_table, saved_frequencies_dropdown
import numpy
from configuration import config_729_tracker as c


class drift_tracker(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.cxn = cxn
        self.subscribed = False
        self.updater = LoopingCall(self.looping_update)
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
        self.entry_table = saved_frequencies_dropdown(self.reactor, limits = c.frequency_limit, suffix = ' MHz', sig_figs = 4)
        self.entry_button = QtGui.QPushButton("Submit")
        self.remove_button = QtGui.QPushButton("Remove")
        self.remove_count = QtGui.QSpinBox()
        self.remove_count.setRange(-20,20)
        self.update_enable = QtGui.QCheckBox()
        self.send_to_semaphroe = QtGui.QCheckBox()
        self.update_rate = QtGui.QSpinBox()
        self.update_rate.setSuffix('sec')
        self.update_rate.setKeyboardTracking(False)
        self.update_rate.setRange(3,60)
        self.track_duration = QtGui.QSpinBox()
        self.track_duration.setKeyboardTracking(False)
        self.track_duration.setSuffix('min')
        self.track_duration.setRange(1, 1000)
        layout.addWidget(self.frequency_table, 0, 0, 2, 1)
        layout.addWidget(self.entry_table, 0, 1 , 1 , 1)
        layout.addWidget(self.entry_button, 1, 1, 1, 1)
        remove_layout = QtGui.QHBoxLayout() 
        remove_layout.addWidget(self.remove_count)
        remove_layout.addWidget(self.remove_button)    
        update_layout = QtGui.QHBoxLayout()
        update_layout.addWidget(QtGui.QLabel("Live Update"))
        update_layout.addWidget(self.update_enable)
        update_layout.addWidget(QtGui.QLabel("Send To Semaphore"))
        update_layout.addWidget(self.send_to_semaphroe)
        update_layout.addWidget(QtGui.QLabel("Rate (sec)"))
        update_layout.addWidget(self.update_rate)
        keep_layout = QtGui.QHBoxLayout()
        keep_layout.addWidget(QtGui.QLabel("Tracking Duration"))
        keep_layout.addWidget(self.track_duration)
        layout.addLayout(update_layout, 2, 1, 1, 1)
        layout.addLayout(remove_layout, 2, 0, 1, 1)
        layout.addLayout(keep_layout, 3, 1, 1, 1)
        return layout
        
    def connect_layout(self):
        self.remove_button.clicked.connect(self.on_remove)
        self.entry_button.clicked.connect(self.on_entry)
        self.track_duration.valueChanged.connect(self.on_new_track_duration)
        self.update_enable.toggled.connect(self.on_update_enable)
        self.update_rate.valueChanged.connect(self.on_update_rate_change)
    
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
            message = QtGui.QMessageBox()
            message.setText(e.msg)
            message.exec_()
    
    @inlineCallbacks
    def on_entry(self, clicked):
        server = self.cxn.servers['SD Tracker']
        info = self.entry_table.get_info()
        with_units = [(name, self.WithUnit(val, 'MHz')) for name,val in info]
        try:
            yield server.set_measurements(with_units)
        except self.Error as e:
            message = QtGui.QMessageBox()
            message.setText(e.msg)
            message.exec_()
    
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
            from connection import connection
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
        xmin,xmax = self.b_drift.get_xlim()
        xmin-= 10
        xmax+= 10
        points = 1000
        x = numpy.linspace(xmin, xmax, points) 
        y = 1000 * numpy.polyval(p, 60*x)
        l = self.b_drift.plot(x, y, '-r')[0]
        self.b_drift_fit_line.append(l)
        b_in_units = p[1] * 1000.0 * 60.0
        a_in_units = p[0] * 1000* (60.0)**2
        c_in_units = p[2] * 1000
        label = self.b_drift.annotate('fit a*x**2 + b*x + c, a: {0:.1f} mgauss/min**2 b: {1:.1f} mgauss/min, c: {2:.1f} mgauss'.format(a_in_units, b_in_units, c_in_units), xy = (0.1, 0.9), xycoords = 'axes fraction', fontsize = 11.0)
        self.b_drift_fit_line.append(label)
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
        self.line_drift_fit_line.append(l)
        b_in_units = p[1] * 1000.0 * 60.0
        a_in_units = p[0] * (1000.0 * 60.0)**2
        label = self.line_drift.annotate('fit a*x**2 + b*x + c, a: {0:.1f} KHz/min**2 b: {1:.1f} KHz/min, c: {2:.4f} MHz'.format(a_in_units, b_in_units, p[2]), xy = (0.1, 0.9), xycoords = 'axes fraction', fontsize = 11.0)
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
    
    @inlineCallbacks
    def looping_update(self):
        new_lines = yield self.update_lines()
        if self.send_to_semaphroe.isChecked() and new_lines is not None:
            try:
                #try changing the center frequency of the lines stored in the semaphore
                have_update = False
                new_lines = dict(new_lines)
                semaphore = self.cxn.servers['Semaphore']
                known_info = yield semaphore.get_parameter(c.saved_lines_729)
                min_freq = known_info[0][1]
                max_freq = known_info[1][1]
                for i in range(2, len(known_info)):
                    name = known_info[i][0]
                    try:
                        new_freq = new_lines[name]
                    except KeyError:
                        pass
                    else:
                        if min_freq <= new_freq <= max_freq and new_freq != known_info[i][1]:
                            #if within range, and not the same as the old one
                            l = list(known_info[i])
                            l[1] = new_freq
                            known_info[i] = tuple(l)
                            have_update = True
                if have_update:
                    yield semaphore.set_parameter(c.saved_lines_729, known_info)
            except self.Error as e:
                message = QtGui.QMessageBox()
                message.setText(e.msg)
                message.exec_()
            
            
    
    def update_track(self, meas, axes, lines):
        #clear
        for i in range(len(lines)):
            line = lines.pop()
            line.remove()
        x = numpy.array([m[0] for m in meas])
        y = [m[1] for m in meas]
        line = axes.plot(x,y, 'b*')[0]
        lines.append(line)
        self.drift_canvas.draw()
        
    def update_spectrum(self, lines):
        #clear
        for i in range(len(self.spectral_lines)):
            line = self.spectral_lines.pop()
            line.remove()
        srt = sorted(lines, key = lambda x: x[1])
        num = len(srt)
        for i, (name, freq) in enumerate(srt):
            line = self.spec.axvline(freq['MHz'], linewidth=1.0, ymin = 0, ymax = 1)
            self.spectral_lines.append(line)
            label = self.spec.annotate(name, xy = (freq['MHz'], 0.9 - i * 0.7 / num), xycoords = 'data', fontsize = 13.0)
            self.spectral_lines.append(label)
        self.spec_canvas.draw()

    def update_listing(self, lines):
        self.frequency_table.fill_out_widget(lines)
        
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
    
    def closeEvent(self, x):
        self.reactor.stop()  
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = drift_tracker(reactor)
    widget.show()
    reactor.run()