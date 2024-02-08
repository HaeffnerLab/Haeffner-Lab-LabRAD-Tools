from PyQt5 import QtCore, QtGui, QtWidgets
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
import numpy
import time

'''
Drift Tracker GUI. 
Version 1.16
'''

class drift_tracker_test(QtWidgets.QWidget):
    def __init__(self, reactor, clipboard = None, cxn = None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.clipboard = clipboard
        self.cxn = cxn
        self.subscribed = False

        self.create_layout()
        self.connect_labrad()
        updater = LoopingCall(self.show_current_center)
        updater.start(0.1)

    def create_layout(self):
        layout = QtWidgets.QGridLayout()
        plot_layout = self.create_drift_layout()
        widget_layout = self.create_widget_layout()
        layout.addLayout(plot_layout, 0, 0, 1, 2)
        layout.addLayout(widget_layout, 1, 0, 1, 2)
        self.setLayout(layout)

    def connect_layout(self):
        self.remove_line_center_button.clicked.connect(self.on_remove_line_center)
        self.entry_center_button.clicked.connect(self.on_entry_center)
        self.track_line_center_duration.valueChanged.connect(self.on_new_line_center_track_duration)
        self.copy_clipboard_button.pressed.connect(self.do_copy_info_to_clipboard)

    def create_drift_layout(self):
        layout = QtWidgets.QVBoxLayout()
        self.fig = Figure()
        self.drift_canvas = FigureCanvas(self.fig)
        self.drift_canvas.setParent(self)  
        gs = gridspec.GridSpec(1, 1, wspace=0.15, left = 0.1, right = 0.9)
        line_drift = self.fig.add_subplot(gs[0, 0])
        line_drift.set_xlabel('Time (min)')
        line_drift.set_ylabel('KHz')
        line_drift.set_title("Line Center Drift")
        self.line_drift = line_drift
        self.line_drift_lines = []
        self.line_drift_fit_line = []
        self.mpl_toolbar = NavigationToolbar(self.drift_canvas, self)
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.drift_canvas)
        return layout

    def create_widget_layout(self):
        layout = QtWidgets.QGridLayout()
        self.entry_center_button = QtWidgets.QPushButton("Submit Line Center")
        self.remove_line_center_button = QtWidgets.QPushButton("Remove Line Center")
        self.copy_clipboard_button = QtWidgets.QPushButton("Copy")

        self.linecenter_entry = QtWidgets.QDoubleSpinBox()
        self.linecenter_entry.setRange(-50000.0, 0.0)
        self.linecenter_entry.setDecimals(6)
        self.linecenter_entry.setSuffix(' kHz')

        self.remove_line_center_count = QtWidgets.QSpinBox()
        self.remove_line_center_count.setRange(-20,20)

        self.track_line_center_duration = QtWidgets.QSpinBox()
        self.track_line_center_duration.setKeyboardTracking(False)
        self.track_line_center_duration.setSuffix('min')
        self.track_line_center_duration.setRange(1, 1000)

        self.current_line_center = QtWidgets.QLineEdit(readOnly = True)
        self.current_line_center.setAlignment(QtCore.Qt.AlignHCenter)


        self.input_line_center_layout = QtWidgets.QHBoxLayout()
        self.input_line_center_layout.addWidget(self.linecenter_entry)
        self.input_line_center_layout.addWidget(self.entry_center_button)

        self.remove_line_center_layout = QtWidgets.QHBoxLayout() 
        self.remove_line_center_layout.addWidget(self.remove_line_center_count)
        self.remove_line_center_layout.addWidget(self.remove_line_center_button)

        self.keep_line_center_layout = QtWidgets.QHBoxLayout()
        self.keep_line_center_layout.addWidget(QtWidgets.QLabel("Tracking Duration (Line Center)"))
        self.keep_line_center_layout.addWidget(self.track_line_center_duration)

        self.show_current_center_layout = QtWidgets.QHBoxLayout()
        self.show_current_center_layout.addWidget(self.current_line_center)
        self.show_current_center_layout.addWidget(self.copy_clipboard_button)

        layout.addLayout(self.show_current_center_layout, 2, 0, 1, 1)
        layout.addLayout(self.input_line_center_layout, 0, 1, 1, 1)
        layout.addLayout(self.remove_line_center_layout, 1, 1, 1, 1)
        layout.addLayout(self.keep_line_center_layout, 2, 1, 1, 1)

        return layout

    @inlineCallbacks
    def initialize_layout(self):
        server = yield self.cxn.get_server('SD Tracker')
        duration_line_center = yield server.history_duration()
        self.track_line_center_duration.blockSignals(True)
        self.track_line_center_duration.setValue(duration_line_center['min'])
        self.track_line_center_duration.blockSignals(False)
        yield self.on_new_fit(None, None)

    @inlineCallbacks
    def do_copy_info_to_clipboard(self):
        try:
            server = yield self.cxn.get_server('SD Tracker')
            center = yield server.get_current_center()
        except Exception as e:
            #no lines available
            pass
        else:
            date = time.strftime('%m/%d/%Y')
            text = '| {0} || {1:.8f} MHz || comment'.format(date,  center['MHz'])
            if self.clipboard is not None:
                self.clipboard.setText(text)

    @inlineCallbacks
    def on_remove_line_center(self, clicked):
        to_remove = self.remove_line_center_count.value()
        server = yield self.cxn.get_server('SD Tracker')
        try:
            yield server.remove_line_center_measurement(to_remove)
        except self.Error as e:
            self.displayError(e.msg)

    @inlineCallbacks
    def on_entry_center(self, clicked):
        server = yield self.cxn.get_server('SD Tracker')
        f_with_units = self.WithUnit(self.linecenter_entry.value()/1.0e3, 'MHz')

        try:
            yield server.set_measurements_with_line_center(f_with_units)

        except self.Error as e:
            self.displayError(e.msg)

    @inlineCallbacks
    def on_new_line_center_track_duration(self, value):
        server = yield self.cxn.get_server('SD Tracker')
        rate_line_center = self.WithUnit(value, 'min')
        yield server.history_duration(rate_line_center)

    @inlineCallbacks
    def show_current_center(self):
        try:
            server = yield self.cxn.get_server('SD Tracker')
            center = yield server.get_current_center()
            center = 'Current Line Center: %.8f MHz'%center.value
            self.current_line_center.setText(center)
        except:
            self.current_line_center.setText('Error')

    @inlineCallbacks
    def connect_labrad(self):
        from labrad.units import WithUnit
        from labrad.types import Error
        self.WithUnit = WithUnit
        self.Error = Error
        if self.cxn is None:
            from common.clients.connection import connection
            self.cxn = connection()
            yield self.cxn.connect(password = '')
        self.context = yield self.cxn.context()
        try:
            yield self.subscribe_tracker()
        except Exception as e:
            self.setDisabled(True)
        self.cxn.add_on_connect('SD Tracker', self.reinitialize_tracker)
        self.cxn.add_on_disconnect('SD Tracker', self.disable)
        self.connect_layout()

    @inlineCallbacks
    def subscribe_tracker(self):
        server = yield self.cxn.get_server('SD Tracker')
        yield server.signal__new_fit(85367, context = self.context)
        yield server.addListener(listener = self.on_new_fit, source = None, ID = 85367, context = self.context)
        yield self.initialize_layout()
        self.subscribed = True
        
    @inlineCallbacks
    def reinitialize_tracker(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('SD Tracker')
        yield server.signal__new_fit(85367, context = self.context)
        if not self.subscribed:
            yield server.addListener(listener = self.on_new_fit, source = None, ID = 85367, context = self.context)
            yield self.initialize_layout()
            self.subscribed = True

    @inlineCallbacks
    def on_new_fit(self, x, y):
        yield self.update_fit()

    @inlineCallbacks
    def update_fit(self):
        try:
            server = yield self.cxn.get_server('SD Tracker')
            history_line_center = yield server.get_fit_history()
            excluded_line_center = yield server.get_excluded_points()
            fit_f = yield server.get_fit_parameters()
        except Exception as e:
            print(e)
            pass
        else:
            inunits_f = [(t['min'], freq['kHz']) for (t,freq) in history_line_center]
            inunits_f_nofit = [(t['min'], freq['kHz']) for (t,freq) in excluded_line_center]
            self.update_track((inunits_f,inunits_f_nofit), self.line_drift, self.line_drift_lines)
            self.plot_fit_f(fit_f)

    def plot_fit_f(self, p):
        for i in range(len(self.line_drift_fit_line)):
            l = self.line_drift_fit_line.pop()
            l.remove()
        xmin,xmax = self.line_drift.get_xlim()
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
        

    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
        
    def displayError(self, text):
        #runs the message box in a non-blocking method
        message = QtWidgets.QMessageBox(self)
        message.setText(text)
        message.open()
        message.show()
        message.raise_()
        
    def closeEvent(self, x):
        self.reactor.stop()   
    
if __name__=="__main__":
    a = QtWidgets.QApplication( [] )
    clipboard = a.clipboard()
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = drift_tracker_test(reactor, clipboard)
    widget.show()
    reactor.run()

