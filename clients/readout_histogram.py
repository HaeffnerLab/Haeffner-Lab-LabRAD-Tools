from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread
import numpy

class config_729_hist(object):
    #IDs for signaling
    ID_A = 99999
    ID_B = 99998
    #data vault comment
    dv_parameter = 'Histogram729'
    #semaphore locations
    readout_threshold_dir =  ('StateReadout','state_readout_threshold')

class readout_histogram(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.cxn = cxn
        self.thresholdVal = None
        self.last_data = None
        self.last_hist = None
        self.subscribed = [False,False]
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
        self.axes.set_xlim(left = 0, right = 100)
        self.axes.set_ylim(bottom = 0, top = 50)
        self.thresholdLine = self.axes.axvline(self.thresholdVal, linewidth=3.0, color = 'r', label = 'Threshold')
        self.axes.legend(loc = 'best')
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.axes.set_title('PMT Readout', fontsize = 22)
        self.fig.tight_layout()
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.canvas)
        return layout
    
    def connect_layout(self):
        self.canvas.mpl_connect('button_press_event', self.on_key_press)
    
    @inlineCallbacks
    def on_key_press(self, event):
        if event.button == 2:
            xval = int(round(event.xdata))
            yield self.thresholdChange(xval)
    
    def on_new_data(self, readout):
        self.last_data = readout
        self.updade_histogram(readout)
    
    def updade_histogram(self, data):
        #remove old histogram
        if self.last_hist is not None:
            self.last_hist.remove()
            #explicitly delete the refrence although not necessary
            del self.last_hist
        self.last_hist = self.axes.bar(data[:,0], data[:,1], width = numpy.max(data[:,0])/len(data[:,0]))
        #redo the limits
        x_maximum = data[:,0].max()
        self.axes.set_xlim(left = 0)
        if x_maximum > self.axes.get_xlim()[1]:
            self.axes.set_xlim(right = x_maximum)
        self.axes.set_ylim(bottom = 0)
        y_maximum = data[:,1].max()
        if y_maximum > self.axes.get_ylim()[1]:
            self.axes.set_ylim(top = y_maximum)
        self.canvas.draw()
    
    @inlineCallbacks
    def thresholdChange(self, threshold):
        #update canvas
        self.update_canvas_line(threshold)
        try:
            server = yield self.cxn.get_server('ParameterVault')
            yield server.set_parameter(config_729_hist.readout_threshold_dir[0], config_729_hist.readout_threshold_dir[1], threshold, context = self.context)
        except Exception, e:
            print e
            yield None
               
    def update_canvas_line(self, threshold):
        self.thresholdLine.remove()
        #explicitly delete the refrence although not necessary
        del self.thresholdLine
        try:
            self.thresholdLine = self.axes.axvline(threshold, ymin=0.0, ymax=100.0, linewidth=3.0, color = 'r', label = 'Threshold')
        except Exception as e:
            #drawing axvline throws an error when the plot is never shown (i.e in different tab)
            print 'Weird singular matrix bug deep inside matplotlib'
        self.canvas.draw()
     
    @inlineCallbacks
    def connect_labrad(self):
        if self.cxn is None:
            from common.clients import connection
            self.cxn = connection.connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            yield self.subscribe_data_vault()
        except Exception,e:
            print e
            self.setDisabled(True)
        try:
            yield self.subscribe_parameter_vault()
        except Exception, e:
            print e
            print 'Not Initially Connected to ParameterVault', e
            self.setDisabled(True)
        yield self.cxn.add_on_connect('Data Vault', self.reinitialize_data_vault)
        yield self.cxn.add_on_connect('ParameterVault', self.reinitialize_parameter_vault)
        yield self.cxn.add_on_disconnect('ParameterVault', self.disable)
        yield self.cxn.add_on_disconnect('Data Vault', self.disable)
        self.connect_layout()
        
    @inlineCallbacks
    def subscribe_data_vault(self):
        dv = yield self.cxn.get_server('Data Vault')
        yield dv.signal__new_parameter_dataset(config_729_hist.ID_A, context = self.context)
        yield dv.addListener(listener = self.on_new_dataset, source = None, ID = config_729_hist.ID_A, context = self.context)
        self.subscribed[0] = True
    
    @inlineCallbacks
    def subscribe_parameter_vault(self): 
        server = yield self.cxn.get_server('ParameterVault')
        yield server.signal__parameter_change(config_729_hist.ID_B, context = self.context)
        yield server.addListener(listener = self.on_parameter_change, source = None, ID = config_729_hist.ID_B, context = self.context)
        init_val = yield server.get_parameter(config_729_hist.readout_threshold_dir[0],config_729_hist.readout_threshold_dir[1], context = self.context)
        self.update_canvas_line(init_val)
        self.subscribed[1] = True
    
    @inlineCallbacks
    def reinitialize_data_vault(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('ParameterVault')
        yield server.signal__new_parameter_dataset(config_729_hist.ID_A, context = self.context)
        if not self.subscribed[0]:
            yield server.addListener(listener = self.on_new_dataset, source = None, ID = config_729_hist.ID_A, context = self.context)
            self.subscribed[0] = True
            
    @inlineCallbacks
    def reinitialize_parameter_vault(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('ParameterVault')
        yield server.signal__parameter_change(config_729_hist.ID_B, context = self.context)
        if not self.subscribed[1]:
            yield server.addListener(listener = self.on_parameter_change, source = None, ID = config_729_hist.ID_B, context = self.context)
            self.subscribed[1] = True
        init_val = yield server.get_parameter(config_729_hist.readout_threshold_dir[0],config_729_hist.readout_threshold_dir[1], context = self.context)
        self.update_canvas_line(init_val)
        
    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None
    
    @inlineCallbacks
    def on_parameter_change(self, signal, parameter_id):
        if parameter_id == config_729_hist.readout_threshold_dir:
            server = yield self.cxn.get_server('ParameterVault')
            init_val = yield server.get_parameter(config_729_hist.readout_threshold_dir[0],config_729_hist.readout_threshold_dir[1], context = self.context)
            self.update_canvas_line(init_val)
            
    @inlineCallbacks
    def on_new_dataset(self, x, y):
        if y[3] == config_729_hist.dv_parameter:
            dv = yield self.cxn.get_server('Data Vault')
            dataset = y[0]
            directory = y[2]
            yield dv.cd(directory, context = self.context)
            yield dv.open(dataset, context = self.context)
            data = yield dv.get( context = self.context)
            data = data.asarray
            yield deferToThread(self.on_new_data, data)
            yield dv.cd([''], context = self.context)
                                          
    def closeEvent(self, x):
        self.reactor.stop()  
    
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = readout_histogram(reactor)
    widget.show()
    reactor.run()