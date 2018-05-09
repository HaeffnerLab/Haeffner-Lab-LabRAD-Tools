from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# this try and except avoids the error "RuntimeError: wrapped C/C++ object of type QWidget has been deleted"
try:
	from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
except:
	from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

from matplotlib.figure import Figure
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread
import time
from sequence_analyzer import sequence_analyzer


class config_visualizer(object):
    #IDs for signaling
    ID = 99995

class pulse_sequence_visualizer(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.cxn = cxn
        self.last_seq_data = None
        self.last_plot = None
        self.subscribed = False
        self.pulserupdates = 0
        self.create_layout()
        self.connect_labrad()
    
    def create_layout(self):
        layout = QtGui.QVBoxLayout()
        plot_layout = self.create_plot_layout()
        layout.addLayout(plot_layout)
        self.setLayout(layout)
   
    def create_plot_layout(self):
        layout = QtGui.QVBoxLayout()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(111)
        # self.axes.set_xlim(left = 0, right = 100)
        # self.axes.set_ylim(bottom = 0, top = 50)
        self.axes.legend(loc = 'best')
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes.set_title('Most Recent Pulse Sequence', fontsize = 22)
        self.fig.tight_layout()
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.canvas)
        return layout
     
    @inlineCallbacks
    def connect_labrad(self):
        if self.cxn is None:
            from common.clients import connection
            self.cxn = connection.connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.subscribe_pulser()
        except Exception, e:
            print e
            self.setDisabled(True)
        yield self.cxn.add_on_connect('Pulser', self.reinitialize_pulser)
        yield self.cxn.add_on_disconnect('Pulser', self.disable)

    @inlineCallbacks
    def subscribe_pulser(self):
        pulser = yield self.cxn.get_server('Pulser')
        yield pulser.signal__sequence_programmed(config_visualizer.ID, context = self.context)
        yield pulser.addListener(listener = self.on_new_sequence, source = None, ID = config_visualizer.ID, context = self.context)
        self.subscribed = True
                
    @inlineCallbacks
    def reinitialize_pulser(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('Pulser')
        yield server.signal__sequence_programmed(config_visualizer.ID, context = self.context)
        if not self.subscribed:
            yield server.addListener(listener = self.on_new_sequence, source = None, ID = config_visualizer.ID, context = self.context)
            self.subscribed = True
        
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
                
    @inlineCallbacks
    def on_new_sequence(self, msg_context, signal):
        writer_context = signal
        pulser = yield self.cxn.get_server('Pulser')
        dds = yield pulser.human_readable_dds(context=writer_context)
        ttl = yield pulser.human_readable_ttl(context=writer_context)
        channels = yield pulser.get_channels(context=writer_context)
        yield deferToThread(self.on_new_seq, dds, ttl, channels)

    def on_new_seq(self, dds, ttl, channels):
        self.last_seq_data = {'DDS':dds, 'TTL':ttl, 'channels':channels}
        self.pulserupdates += 1

        sequence = sequence_analyzer(ttl, dds, channels)
        
        self.axes.clear()
        sequence.create_full_plot(self.axes)
        self.axes.set_xlabel('Time (ms)')
        self.axes.set_title('Most Recent Pulse Sequence, ' + time.strftime('%Y-%m-%d %H:%M:%S'))
        self.canvas.draw()

    def closeEvent(self, x):
        self.reactor.stop()  
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = pulse_sequence_visualizer(reactor)
    widget.show()
    reactor.run()