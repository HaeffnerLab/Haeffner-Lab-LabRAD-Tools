'''
Window containing two by two graphs in a grid
'''
import sys
from PyQt4 import QtGui
from GraphWidgetPyQtGraph import Graph_PyQtGraph as Graph
from ScrollingGraphWidgetPyQtGraph import ScrollingGraph_PyQtGraph as ScrollingGraph
import GUIConfig
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import blockingCallFromThread

class QuadGraphWindow(QtGui.QWidget):
    def __init__(self, g1, g2, g3, g4, reactor, parent=None):
        super(QuadGraphWindow, self).__init__(parent)
        self.reactor = reactor        
        self.initUI(g1, g2, g3, g4)
        self.show()

    def initUI(self, g1, g2, g3, g4):
        reactor = self.reactor

        layout = QtGui.QGridLayout()
        layout.addWidget(g1, 0, 0)
        layout.addWidget(g2, 0, 1)
        layout.addWidget(g3, 1, 0)
        layout.addWidget(g4, 1, 1)
        self.setLayout(layout)
