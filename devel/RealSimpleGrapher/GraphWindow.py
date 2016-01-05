'''
Window for holding Graphs
'''
import sys
from PyQt4 import QtGui
from GraphWidgetPyQtGraph import Graph_PyQtGraph as Graph
from ScrollingGraphWidget import ScrollingGraph
import GUIConfig
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import blockingCallFromThread

class GraphWindow(QtGui.QTabWidget):
    def __init__(self, reactor, parent=None):
        super(GraphWindow, self).__init__(parent)
        self.reactor = reactor        
        self.initUI()
        self.show()
        
    def initUI(self):
        reactor = self.reactor

        self.graphDict = {}
        for t, ylim in GUIConfig.tabs.iteritems():
            g = Graph(t, reactor)
            self.graphDict[t] = g
            self.addTab(g, t)
            g.set_ylimits(ylim)
            
        g = ScrollingGraph('scroll', reactor)
        self.graphDict['scroll'] = g
        self.addTab(g, 'scroll')
        g.set_ylimits([0,1])
        for i in range(4):
            self.setCurrentIndex(i)
        self.setCurrentIndex(-1)
        #self.currentChanged.connect(self.onTabChange)

    def insert_tab(self, t):
        g = Graph(t, reactor)
        self.graphDict[t] = g
        self.addTab(g, t)

    def onTabChange(self):
        for t, g in self.graphDict.iteritems():
            g.redraw()
        
    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    main = GraphWindow(reactor)
    main.show()
    #sys.exit(app.exec_())
    reactor.run()
