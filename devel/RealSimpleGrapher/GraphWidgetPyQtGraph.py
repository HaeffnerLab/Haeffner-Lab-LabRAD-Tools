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
from numpy import random

class artistParameters():
    def __init__(self, artist, dataset, index, shown):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown

class Graph_PyQtGraph(QtGui.QWidget):
    def __init__(self, name, reactor, parent=None):
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
        self.coords = QtGui.QLineEdit()
        #self.coords.setText('test')
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.tracelist)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.pw)
        vbox.addWidget(self.coords)
        hbox.addLayout(vbox)
        self.setLayout(hbox)
        self.legend = self.pw.addLegend()
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.plot([],[])
        #vb = self.pw.addViewBox()
        vb = self.pw.plotItem.vb
        self.img = pg.ImageItem(np.random.normal(size=(1,1)))
        vb.addItem(self.img)
        #vb.addItem(self.coords)
        self.pw.scene().sigMouseMoved.connect(self.mouseMoved)

    def update_figure(self):
        for ident, params in self.artists.iteritems():
            if params.shown:
                index = params.index
                x = params.dataset.data[:,0]
                y = params.dataset.data[:,index+1]
                params.artist.setData(x,y)

    def add_artist(self, ident, dataset, index):
        line = self.pw.plot([], [], pen = self.colorChooser.next(), name=ident)
        self.artists[ident] = artistParameters(line, dataset, index, True)
        self.tracelist.addTrace(ident)

    def display(self, ident, shown):
        try:
            artist = self.artists[ident].artist
            if shown:
                self.pw.addItem(artist)
                self.artists[ident].shown = True
            else:
                self.pw.removeItem(artist)
                self.legend.removeItem(ident)
                self.artists[ident].shown = False
        except KeyError:
            raise Exception('404 Artist not found')

    def checkboxChanged(self):
        for ident, item in self.tracelist.trace_dict.iteritems():
            if item.checkState() and not self.artists[ident].shown:
               self.display(ident, True)
            if not item.checkState() and self.artists[ident].shown:
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

    def mouseMoved(self, pos):
        #print "Image position:", self.img.mapFromScene(pos)
        pnt = self.img.mapFromScene(pos)
        string = '(' + str(pnt.x()) + ' , ' + str(pnt.y()) + ')'
        self.coords.setText(string)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    main = Graph_PyQtGraph('example', reactor)
    main.show()
    #sys.exit(app.exec_())
    reactor.run()
