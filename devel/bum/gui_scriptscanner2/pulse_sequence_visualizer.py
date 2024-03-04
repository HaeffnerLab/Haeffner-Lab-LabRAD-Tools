from PyQt5 import QtGui, QtWidgets
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
from .sequence_analyzer import sequence_analyzer


"""
This file is a LabRAD client. It uses twisted to asynchronously request and receive information from a LabRAD server, the pulser, which stores (and executes) pulse sequence information.
The client manifests as a QtGui widget, which is embedded in the experimental GUI. The widget displays a matplotlib plot. Each time the pulser receives a new pulse sequence, this client
receives that information, creates a sequence_analyzer object instance (defined in sequence_analyzer.py), which it calls self.sequence, and uses that object to update that widget's plot to a visualization of the current pulse sequence.
The matploblib plot that this widget displays also tracks mouse movement events via mpl_connect. If the cursor hovers over one of the dds_box objects stored in the list self.sequence.dds_boxes, then the below-defined function "hover" is called.
In doing so it displays an annotation which allows the user to view information about that pulse, which is stored in the dds_box object.
"""




class config_visualizer(object):
    #ID for signaling
    ID = 99995

class pulse_sequence_visualizer(QtWidgets.QWidget):
    def __init__(self, reactor, cxn = None, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        # Initialize
        self.reactor = reactor
        self.cxn = cxn
        self.last_seq_data = None
        self.last_plot = None
        self.subscribed = False
        self.current_box = None
        self.mpl_connection = None
        self.create_layout()
        self.connect_labrad()
    
    def create_layout(self):
        # Creates GUI layout
        layout = QtWidgets.QVBoxLayout()
        plot_layout = self.create_plot_layout()
        layout.addLayout(plot_layout)
        self.setLayout(layout)
   
    def create_plot_layout(self):
        # Creates empty matplotlib plot layout
        layout = QtWidgets.QVBoxLayout()
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.axes = self.fig.add_subplot(111)
        self.axes.legend(loc = 'best')
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes.set_title('Most Recent Pulse Sequence', fontsize = 22)
        self.axes.set_xlabel('Time (ms)')
        self.fig.tight_layout()
        # Create an empty an invisible annotation, which will be moved around and set to visible later when needed
        self.annot = self.axes.annotate("", xy=(0,0), xytext=(-0.5,0.5),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="w"), horizontalalignment='center', 
            multialignment='left', 
            verticalalignment='center')
        self.annot.get_bbox_patch().set_alpha(0.8)
        self.annot.set_visible(False)
        # Add the canvas to the GUI widget.
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.canvas)
        return layout
     
    @inlineCallbacks
    # Attempt to connect ot the pulser server 
    def connect_labrad(self):
        if self.cxn is None:
            from common.clients import connection
            self.cxn = connection.connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.subscribe_pulser()
        except Exception as e:
            print(e)
            self.setDisabled(True)
        yield self.cxn.add_on_connect('Pulser', self.reinitialize_pulser)
        yield self.cxn.add_on_disconnect('Pulser', self.disable)

    @inlineCallbacks
    # Asynchronously subscribe to the pulser server, listing the below-defined function "on_new_sequence" as the function to execute when a signal is received
    def subscribe_pulser(self):
        pulser = yield self.cxn.get_server('Pulser')
        yield pulser.signal__sequence_programmed(config_visualizer.ID, context = self.context)
        yield pulser.addListener(listener = self.on_new_sequence, source = None, ID = config_visualizer.ID, context = self.context)
        self.subscribed = True
                
    @inlineCallbacks
    # Reinitializes subsciption to pulser if necessary
    def reinitialize_pulser(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('Pulser')
        yield server.signal__sequence_programmed(config_visualizer.ID, context = self.context)
        if not self.subscribed:
            yield server.addListener(listener = self.on_new_sequence, source = None, ID = config_visualizer.ID, context = self.context)
            self.subscribed = True
        
    @inlineCallbacks
    # Client's disable functionality
    def disable(self):
        self.setDisabled(True)
        yield None
                
    @inlineCallbacks
    def on_new_sequence(self, msg_context, signal):
        # This function is called when a "new pulse sequence" signal is received from the pulser.
        # Store time when signal was received
        signal_time = time.localtime()
        writer_context = signal
        # Asynchronously request pulse sequence information from the pulser
        pulser = yield self.cxn.get_server('Pulser')
        dds = yield pulser.human_readable_dds(context=writer_context)
        ttl = yield pulser.human_readable_ttl(context=writer_context)
        channels = yield pulser.get_channels(context=writer_context)
        # Call the function "on_new_seq" to process this information
        yield deferToThread(self.on_new_seq, dds, ttl, channels, signal_time)

    def on_new_seq(self, dds, ttl, channels, signal_time):

        
        # Temporary stop tracking mouse movement
        if self.mpl_connection:
            self.canvas.mpl_disconnect(self.mpl_connection)
        self.last_seq_data = {'DDS':dds, 'TTL':ttl, 'channels':channels}
        # Create sequence_analyzer object instance
        self.sequence = sequence_analyzer(ttl, dds, channels)
        # Clear the plot of all drawn objects

        self.clear_plot()

        # Call the sequence_analyzer object's create_full_plot method to draw the plot on the GUI's axes.
        self.sequence.create_full_plot(self.axes)
        self.axes.set_title('Most Recent Pulse Sequence, ' + time.strftime('%Y-%m-%d %H:%M:%S', signal_time))
        # Draw and reconnect to mouse hover events
        
        self.canvas.draw_idle()
        self.mpl_connection = self.canvas.mpl_connect("motion_notify_event", self.hover)


    def clear_plot(self):
        # Remove all lines, boxes, and annotations, except for the hover annotation
        for child in self.axes.get_children():
            if isinstance(child, (matplotlib.lines.Line2D, matplotlib.text.Annotation, matplotlib.collections.PolyCollection)):
                if child is not self.annot:
                    child.remove()

    def format_starttime(self, t):
        # Function for formatting times in the hover annotation
        if round(1e6*t) < 1000:
            return '{:.1f} $\mu$s'.format(1e6*t)
        else:
            return '{:.3f} ms'.format(1e3*t)

    def format_duration(self, t):
        # Function for formatting times in the hover annotation
        if round(1e6*t) < 1000:
            return '%#.4g $\mu$s' % (1e6*t)
        else:
            return '%#.4g ms' % (1e3*t)

    def update_annot(self, dds_box):
        # This function updates the text of the hover annotation.
        drawx = 1e3*(dds_box.starttime() + dds_box.duration()/2.0)
        drawy = dds_box.offset + dds_box.scale/2.0
        self.annot.xy = (drawx, drawy)
        text = '{0}\nStart: {1}\nDuration: {2}\n{3:.4f} MHz\n{4:.2f} dBm'.format(dds_box.channel,
                                                                                self.format_starttime(dds_box.starttime()),
                                                                                self.format_duration(dds_box.duration()),
                                                                                dds_box.frequency(),
                                                                                dds_box.amplitude())
        self.annot.set_text(text)

    def hover(self, event):
        # This function is called when the mouse moves
        # It updates the hover annotation if necessary.
        (self.last_mouse_x, self.last_mouse_y) = (event.x, event.y)
        vis = self.annot.get_visible()
        if event.inaxes == self.axes:
            for dds_box in self.sequence.dds_boxes:
                if dds_box.box.contains(event)[0]:
                    if dds_box is not self.current_box:
                        self.current_box = dds_box
                        self.update_annot(dds_box)
                        self.annot.set_visible(True)
                        self.canvas.draw_idle()
                    break
                else:
                    self.current_box = None
                    if vis:
                        self.annot.set_visible(False)
                        self.canvas.draw_idle()
        else:
            self.current_box = None


    def closeEvent(self, x):
        self.reactor.stop()  
    
if __name__=="__main__":
    a = QtWidgets.QApplication( [] )
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    widget = pulse_sequence_visualizer(reactor)
    widget.show()
    reactor.run()
