'''
Window containing two side by side graphs
'''
import sys
from PyQt4 import QtGui
from GraphWidgetPyQtGraph import Graph_PyQtGraph as Graph
from ScrollingGraphWidgetPyQtGraph import ScrollingGraph_PyQtGraph as ScrollingGraph
import GUIConfig
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import blockingCallFromThread

class DoubleGraphWindow(QtGui.QWidget):
    def __init__(self, g1, g2, reactor, parent=None):
        super(DoubleGraphWindow, self).__init__(parent)
        self.reactor = reactor        
        self.initUI(g1, g2)
        self.show()

    def initUI(self, g1, g2):
        reactor = self.reactor

        layout = QtGui.QHBoxLayout()
        layout.addWidget(g1)
        layout.addWidget(g2)
        self.setLayout(layout)
