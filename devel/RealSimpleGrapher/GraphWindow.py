'''
Window for holding Graphs
'''
import sys
from PyQt4 import QtGui
import GUIConfig
from GraphWidgetPyQtGraph import Graph_PyQtGraph as Graph
from ScrollingGraphWidgetPyQtGraph import ScrollingGraph_PyQtGraph as ScrollingGraph
from GridGraphWindow import GridGraphWindow

class GraphWindow(QtGui.QTabWidget):
    def __init__(self, reactor, parent=None):
        super(GraphWindow, self).__init__(parent)
        self.reactor = reactor        
        self.initUI()
        self.show()
        
    def initUI(self):
        reactor = self.reactor
        self.graphDict = {}
        self.tabDict = {}

        for gc in GUIConfig.tabs:
            gcli = gc.config_list
            gli = []
            for config in gcli:
                name = config.name
                max_ds = config.max_datasets
                if config.isScrolling:
                    g = ScrollingGraph(config, reactor)
                else:
                    print "config: ", config 
                    g = Graph(config, reactor)
                g.set_ylimits(config.ylim)
                self.graphDict[name] = g
                gli.append(g)
            widget = GridGraphWindow(gli, gc.row_list, gc.column_list, reactor)
            self.tabDict[name] = widget
            self.addTab(widget, gc.tab)
            self.setMovable(True)
            

    def insert_tab(self, t):
        g = Graph(t, reactor)
        self.graphDict[t] = g
        self.addTab(g, t)
        
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
