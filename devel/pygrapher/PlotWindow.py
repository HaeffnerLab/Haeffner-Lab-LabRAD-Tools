from PyQt4 import QtCore, QtGui
# import pyqtgraph as pg
import numpy as np
from DatasetList import DatasetList
from util import color_chooser
from basic_plotter import Basic_Matplotlib_Plotter
from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall

import time

import IPython as ip

# pg.setConfigOption('background', 'w')
# pg.setConfigOption('foreground', 'k')

class dataset_info(object):
    '''stores information about the dataset'''
    plot_item = None
    legend_items = None
    
class PlotWindow(QtGui.QWidget):
    '''
    class for the window consisting of many plots
    '''
    #signal gets called when the user removes a dataset from the plot window
    on_dataset_removed = QtCore.pyqtSignal()
    
    def __init__(self, reactor):
        super(PlotWindow, self).__init__()
        QtCore.pyqtRemoveInputHook()
        #dictionary in the form dataset_name: dataset_info
        self.reactor = reactor
        self.datasets = {}
        self.setup_layout()
        self.connect_layout()
        self.colors = color_chooser()

    def new_dataset(self, dataset):
        self.datasets[dataset.datasetName] = dataset
        self.plot_widget.add_artist(dataset.datasetName)
        print "added artist " + dataset.datasetName
        self.dataset_list.add_dataset(dataset)
        #ip.embed()
        #dataset.getData()
        #yield deferToThread(time.sleep, 0.1)
        #try:
        #    xdata =  dataset.xdata
        #    ydata = dataset.ydata
        #except AttributeError:
        #    xdata = []
        #    ydata = []
        #self.plot_widget.set_data(dataset.datasetName, (xdata, ydata))

    #@inlineCallbacks
    def new_data(self, dataset):
        '''
        Check the dataset for new data
        '''
        xdata = dataset.xdata
        ydata = dataset.ydata
        self.plot_widget.set_data(dataset.datasetName, (xdata, ydata))
        
    def new_parameters(self, parameters):
        #if window name is one of these, self.plot_widget.setTitle('first plot!')
        pass
        
    def setup_layout(self):
        '''
        adds a new plot widget to the layout made in the ui file
        '''
        layout = QtGui.QHBoxLayout()
        self.dataset_list = DatasetList()
        layout.addWidget(self.dataset_list)
        self.plot_widget = Basic_Matplotlib_Plotter()
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)
    
    def connect_layout(self):
#       self.dataset_list.on_dataset_checked.connect(self.user_dataset_checked)
        self.dataset_list.keep_button.pressed.connect(self.on_change)
        self.dataset_list.move_button.pressed.connect(self.test_hide)
    
    def test_hide(self):
        #self.plot_widget.hide('1', False)
        ip.embed()
    
        
    @inlineCallbacks
    def on_change(self):
        value = 1
        self.plot_widget.add_artist(str(value))
        for i in range(100):
            yield deferToThread(time.sleep, 0.1)
            x_data = np.arange(i)
            y_data = np.arange(i)
            self.plot_widget.set_data(str(value), (x_data+value, y_data))

    def closeEvent(self, event):
        self.plot_widget.handle_close()
        super(PlotWindow, self).closeEvent(event)
        self.reactor.stop()
                                  
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    import qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    latticeGUI = PlotWindow(reactor)
    latticeGUI.setWindowTitle('Grapher')
    latticeGUI.show()
    reactor.run()
