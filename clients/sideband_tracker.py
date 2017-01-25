# sideband tracker

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
import numpy as np
import time

class sideband_tracker(QtGui.QWidget):
    def __init__(self, reactor, cxn = None, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.reactor = reactor
        self.cxn = cxn
        
        self.create_layout()

    def create_layout(self):
        layout = QtGui.QGridLayout()
        plot_layout = self.create_drift_layout()

        layout.addLayout(plot_layout, 0, 0, 1, 2)

        self.setLayout(layout)


    def create_drift_layout(self):

        layout = QtGui.QVBoxLayout()
        self.fig = Figure()

        self.drift_canvas = FigureCanvas(self.fig)
        self.drift_canvas.setParent(self)  
        gs = gridspec.GridSpec(1, 2, wspace=0.15, left = 0.05, right = 0.95)
        line_1 = self.fig.add_subplot(gs[0, 0])
        line_1.set_xlabel('Time (min)')
        line_1.set_ylabel('KHz')
        line_1.set_title("Radial 1")

        line_2 = self.fig.add_subplot(gs[0, 1], sharex = line_1)
        line_2.set_xlabel('Time (min)')
        line_2.set_ylabel('KHz')
        line_2.set_title("Radial 2")

        self.line_1_lines = []
        self.line_2_lines = []
        self.line_1_fit_line = []
        self.line_2_fit_line = []

        self.mpl_toolbar = NavigationToolbar(self.drift_canvas, self)
        layout.addWidget(self.mpl_toolbar)
        layout.addWidget(self.drift_canvas)
        return layout

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
    widget = sideband_tracker(reactor)
    widget.show()
    reactor.run()



        

        

