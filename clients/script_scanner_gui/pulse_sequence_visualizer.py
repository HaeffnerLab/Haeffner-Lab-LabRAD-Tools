from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# this try and except avoids the error "RuntimeError: wrapped C/C++ object of type QWidget has been deleted"
try:
	from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
except:
	from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

import matplotlib
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
        self.has_hovered = False
        self.xx = 0
        self.yy = 0
        self.current_box = None
        self.mpl_connection = None
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
        self.axes.legend(loc = 'best')
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes.set_title('Most Recent Pulse Sequence', fontsize = 22)
        self.axes.set_xlabel('Time (ms)')
        self.fig.tight_layout()

        self.annot = self.axes.annotate("", xy=(0,0), xytext=(-0.5,0.5),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"), horizontalalignment='center', multialignment='left', verticalalignment='center')
        self.annot.get_bbox_patch().set_alpha(0.8)
        self.annot.set_visible(False)

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
        signal_time = time.localtime()
        writer_context = signal
        pulser = yield self.cxn.get_server('Pulser')
        dds = yield pulser.human_readable_dds(context=writer_context)
        ttl = yield pulser.human_readable_ttl(context=writer_context)
        channels = yield pulser.get_channels(context=writer_context)
        yield deferToThread(self.on_new_seq, dds, ttl, channels, signal_time)

    def on_new_seq(self, dds, ttl, channels, signal_time):
        if self.mpl_connection:
            self.canvas.mpl_disconnect(self.mpl_connection)

        self.last_seq_data = {'DDS':dds, 'TTL':ttl, 'channels':channels}

        self.sequence = sequence_analyzer(ttl, dds, channels)
        
        self.clear_plot()
        self.sequence.create_full_plot(self.axes)

        # self.whateverline = self.axes.lines[0]
        # self.annot.set_visible(False)
        # self.canvas.mpl_connect("draw_event", self.draw)

        # self.axes.set_xlabel('Time (ms)')
        self.axes.set_title('Most Recent Pulse Sequence, ' + time.strftime('%Y-%m-%d %H:%M:%S', signal_time))
        self.canvas.draw()

        self.mpl_connection = self.canvas.mpl_connect("motion_notify_event", self.hover)



    def clear_plot(self):
        # for line in self.axes.lines:
        #     line.remove()
        for child in self.axes.get_children():
            # print child
            if isinstance(child, (matplotlib.lines.Line2D, matplotlib.text.Annotation, matplotlib.collections.PolyCollection)):
                if child is not self.annot:
                    child.remove()


    def format_starttime(self, t):
        if round(1e6*t) < 1000:
            return '{:.1f} $\mu$s'.format(1e6*t)
        else:
            return '{:.3f} ms'.format(1e3*t)

    def format_duration(self, t):
        if round(1e6*t) < 1000:
            return '%#.4g $\mu$s' % (1e6*t)
        else:
            return '%#.4g ms' % (1e3*t)

    def update_annot(self, dds_box):
        drawx = 1e3*(dds_box.starttime() + dds_box.duration()/2.0)
        drawy = dds_box.offset + dds_box.scale/2.0
        self.annot.xy = (drawx, drawy)
        text = '{0}\nStart: {1}\nDuration: {2}\n{3:.4f} MHz\n{4:.2f} dBm'.format(dds_box.channel,
                                                                                self.format_starttime(dds_box.starttime()),
                                                                                self.format_duration(dds_box.duration()),
                                                                                dds_box.frequency(),
                                                                                dds_box.amplitude())
        self.annot.set_text(text)

    # def draw(self, event):
    #     if self.has_hovered:
    #         self.canvas.motion_notify_event(self.last_mouse_x, self.last_mouse_y)

    def hover(self, event):
        # if not self.has_hovered: self.has_hovered = True
        (self.last_mouse_x, self.last_mouse_y) = (event.x, event.y)

        # print(event.x, event.y)
        vis = self.annot.get_visible()

        if event.inaxes == self.axes:
            for dds_box in self.sequence.dds_boxes:
                if dds_box.box.contains(event)[0]:
                    if dds_box is not self.current_box:
                        # t1 = time.time()
                        self.current_box = dds_box
                        self.update_annot(dds_box)
                        self.annot.set_visible(True)
                        self.canvas.draw_idle()
                        # t2 = time.time()
                    break
                else:
                    self.current_box = None
                    if vis:
                        self.annot.set_visible(False)
                        self.canvas.draw_idle()
        else:
            self.current_box = None


            # cont, ind = self.whateverline.contains(event)
            # if cont:
            #     self.update_annot(self.whateverline, ind)
            #     # self.update_annot(ind)
            #     self.annot.set_visible(True)
            #     self.canvas.draw_idle()
            #     # self.canvas.draw()
            # else:
            #     if vis:
            #         self.annot.set_visible(False)
            #         self.canvas.draw_idle()
            #         # self.canvas.draw()








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