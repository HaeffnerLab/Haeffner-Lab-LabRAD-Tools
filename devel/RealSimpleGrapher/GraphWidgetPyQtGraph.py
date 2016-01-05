import sys
from PyQt4 import QtGui
import pyqtgraph as pg
from TraceListWidget import TraceList
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import blockingCallFromThread
import itertools
from Dataset import Dataset

import numpy as np

class Graph_PyQtGraph(QtGui.QWidget):
    def __init__(self, name, reactor, parent=None, ylim=[0,1]):
        super(Graph_PyQtGraph, self).__init__(parent)
        self.reactor = reactor
        self.artists = {}
        self.datasets = {} # a single dataset might have multiple traces
        self.should_stop = False
        self.name = name
        self.live_update_loop = LoopingCall(self.update_figure)
        self.live_update_loop.start(0)

        colors = ['r', 'g', 'b']
        self.colorChooser = itertools.cycle(colors)
        self.initUI()

    def initUI(self):
        self.tracelist = TraceList()
        self.pw = pg.PlotWidget()
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.tracelist)
        hbox.addWidget(self.pw)
        self.setLayout(hbox)
        self.legend = self.pw.addLegend()
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.plot([],[])

    def update_figure(self):
        for ident, (artist, dataset, index, shown) in self.artists.iteritems():
            if shown:
                x = dataset.data[:,0]
                y = dataset.data[:,index+1]
                artist.setData(x,y)

    def add_artist(self, ident, dataset, index):
        line = self.pw.plot([], [], pen = self.colorChooser.next(), name=ident)
        self.artists[ident] = [line, dataset, index, True]
        self.tracelist.addTrace(ident)

    def display(self, ident, shown):
        try:
            artist = self.artists[ident][0]
            if shown:
                self.pw.addItem(artist)
                self.artists[ident][3] = True
            else:
                self.pw.removeItem(artist)
                self.legend.removeItem(ident)
                self.artists[ident][3] = False
        except KeyError:
            raise Exception('404 Artist not found')

    def checkboxChanged(self, state):
        for ident, item in self.tracelist.trace_dict.iteritems():
            if item.checkState():
               self.display(ident, True)
            else:
                self.display(ident, False)

    @inlineCallbacks
    def add_dataset(self, dataset):
        labels = yield dataset.getLabels()
        for i, label in enumerate(labels):
            self.add_artist(label, dataset, i)

    def set_xlimits(self, limits):
        self.pw.setXRange(limits[0], limits[1])
        self.current_limits = limits

    def set_ylimits(self, limits):
        self.pw.setYRange(limits[0],limits[1])  

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    main = Graph_PyQtGraph('example', reactor)
    main.show()
    #sys.exit(app.exec_())
    reactor.run()
