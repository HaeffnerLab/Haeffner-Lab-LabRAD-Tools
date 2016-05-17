import sys
from PyQt4 import QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from TraceListWidget import TraceList
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from twisted.internet.threads import blockingCallFromThread

from Dataset import Dataset

import numpy as np


class Graph(QtGui.QWidget):
    def __init__(self, name, reactor, parent=None, ylim=[0,1]):
        super(Graph, self).__init__(parent)
        self.reactor = reactor
        self.artists = {}
        self.datasets = {} # a single dataset might have multiple traces
        self.should_stop = False
        self.name = name
        self.initUI(ylim)

    def initUI(self, ylim):
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.tracelist = TraceList()

        self.ax = self.figure.add_subplot(111)
        self.ani = animation.FuncAnimation(self.figure, self.update_figure, self.should_continue, init_func=self.init, interval=25, blit=False)

        self.ax.set_xlim([0, 100])
        self.ax.set_ylim(ylim)
        self.ax.set_title(self.name)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.tracelist)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.canvas)
        hbox.addLayout(vbox)
        self.setLayout(hbox)
        #self.draw_stuff()

    def init(self):
        line, = self.ax.plot([], [])
        return line,

    def update_figure(self, _input = None):
        artists = []
        for ident, (artist, dataset, index) in self.artists.iteritems():
            x = dataset.data[:,0]
            y = dataset.data[:,index+1]
            artist.set_data((x,y))
            artists.append(artist)
        return artists

    def add_artist(self, ident, dataset, index):
        line, = self.ax.plot([], [], '-o', markersize = 1.0, label = ident)
        #self.ax.legend()
        # dataset is the dataset object
        # index is the position in the dataset object this trace lives
        self.artists[ident] = [line, dataset, index]
        self.tracelist.addTrace(ident)

        # connect the checkbox in the tracelist
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        #cb = self.tracelist.trace_dict[ident]
        #cb.itemChanged.connect(self.checkboxChanged)

    def display(self, ident, shown):
        try:
            self.artists[ident][0].set_visible(shown)
        except KeyError:
            raise Exception('404 Artist not found')
        self.canvas.draw()

    def checkboxChanged(self, state):
        for ident, item in self.tracelist.trace_dict.iteritems():
            if item.checkState():
               self.display(ident, True)
            else:
                self.display(ident, False)

    def should_continue(self):
        while True:
            if self.should_stop: return
            yield True

    @inlineCallbacks
    def add_dataset(self, dataset):
        labels = yield dataset.getLabels()
        for i, label in enumerate(labels):
            self.add_artist(label, dataset, i)

    def set_xlimits(self, limits):
        self.ax.set_xlim(limits)
        self.current_limits = limits

    def set_ylimits(self, limits):
        self.ax.set_ylim(limits)

    def redraw(self):
        self.canvas.draw()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    main = Graph('example', reactor)
    main.show()
    #sys.exit(app.exec_())
    reactor.run()
