import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from .TraceListWidget import TraceList
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
import itertools
from .Dataset import Dataset
from random import shuffle
import queue

import numpy as np
from numpy import random

class artistParameters():
    def __init__(self, artist, dataset, index, shown):
        self.artist = artist
        self.dataset = dataset
        self.index = index
        self.shown = shown
        self.last_update = 0 # update counter in the Dataset object
                             # only redraw if the dataset has a higher
                             # update count

class Graph_PyQtGraph(QtWidgets.QWidget):
    def __init__(self, config, reactor, parent=None):
        super(Graph_PyQtGraph, self).__init__(parent)
        self.reactor = reactor
        self.artists = {}
        self.should_stop = False
        self.name = config.name
        self.show_points = config.show_points
        self.grid_on = config.grid_on
 
        self.dataset_queue = queue.Queue(config.max_datasets)
        
        self.live_update_loop = LoopingCall(self.update_figure)
        self.live_update_loop.start(0)
        
    
        colors = [(47,126,243), (250,138,39), (96,233,128), (255,77,77), (255,51,153), (128,255,0), (255,241,102),
                  (255,128,128), (255,255,192), (255,255,64), (0,255,0), (64, 255,255), (0,128, 255), (192,64,192),
                  (255,255,255), (64, 0, 255), (128,128,128)]
        # colors = [(128,0,0),(170,110,40),(128,128,0),(0,128,128),(0,0,128),(230,25,75),(245,130,48),(255,255,25),
        #           (2190,245,60),(60,180,75),(70,240,240),(0,130,200),(145,30,180),(240,50,230),(128,128,128),
        #           (250,190,190),(255,215,180),(255,250,200),(170,255,195),(230,190,255),(255,255,255)]
        #colors = ['r', 'g', 'y', 'c', 'm', 'w']
        shuffle(colors)
        self.colorChooser = itertools.cycle(colors)
        self.initUI()

    def initUI(self):
        self.tracelist = TraceList(self)
        self.pw = pg.PlotWidget()
        self.coords = QtWidgets.QLabel('')
        self.title = QtWidgets.QLabel(self.name)
        frame = QtWidgets.QFrame()
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.tracelist)
        hbox = QtWidgets.QHBoxLayout()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.title)
        vbox.addWidget(self.pw)
        vbox.addWidget(self.coords)
        frame.setLayout(vbox)
        splitter.addWidget(frame)
        hbox.addWidget(splitter)
        self.setLayout(hbox)
        #self.legend = self.pw.addLegend()
        self.tracelist.itemChanged.connect(self.checkboxChanged)
        self.pw.plot([0],[0])
        vb = self.pw.plotItem.vb
        self.img = pg.ImageItem()
        vb.addItem(self.img)
        self.pw.scene().sigMouseMoved.connect(self.mouseMoved)
        self.pw.sigRangeChanged.connect(self.rangeChanged)

    def update_figure(self):
        for ident, params in self.artists.items():
            if params.shown:
                try:
                    ds = params.dataset
                    index = params.index
                    current_update = ds.updateCounter
                    if params.last_update < current_update:
                        # adding the sort 
                        
                        x = ds.data[:,0]
                        y = ds.data[:,index+1]
                        # some scans are 
#                         inds = np.argsort(x)
#                         x=x[inds]
#                         y=y[inds]
#                         
                        params.last_update = current_update
                        params.artist.setData(x,y)
                except: pass

    def add_artist(self, ident, dataset, index, no_points = False):
        '''
        no_points is an override parameter to the global show_points setting.
        It is to allow data fits to be plotted without points
        '''
        new_color = next(self.colorChooser)
        if self.show_points and not no_points:
            line = self.pw.plot([0], [0], symbol='o', symbolBrush = new_color, pen = new_color, name = ident)
        else:
            line = self.pw.plot([0], [0], pen = new_color, name = ident)
    if self.grid_on:
       self.pw.showGrid(x=True, y=True)
       self.artists[ident] = artistParameters(line, dataset, index, True)
       self.tracelist.addTrace(ident , color = new_color )

    def remove_artist(self, ident):
        try:
            artist = self.artists[ident].artist
            self.pw.removeItem(artist)
            #self.legend.removeItem(ident)
            self.tracelist.removeTrace(ident)
            self.artists[ident].shown = False
            try:
                del self.artists[ident]
            except KeyError:
                pass
        except:
            print("remove failed")

    def display(self, ident, shown):
        try:
            artist = self.artists[ident].artist
            if shown:
                self.pw.addItem(artist)
                self.artists[ident].shown = True
            else:
                self.pw.removeItem(artist)
                #self.legend.removeItem(ident)
                self.artists[ident].shown = False
        except KeyError:
            raise Exception('404 Artist not found')

    def checkboxChanged(self):
        for ident, item in self.tracelist.trace_dict.items():
            try:
                if item.checkState() and not self.artists[ident].shown:
                    self.display(ident, True)
                if not item.checkState() and self.artists[ident].shown:
                    self.display(ident, False)
            except KeyError: # this means the artist has been deleted.
                pass

    def rangeChanged(self):
        lims = self.pw.viewRange()
        self.pointsToKeep =  lims[0][1] - lims[0][0]
        self.current_limits = [lims[0][0], lims[0][1]]

    @inlineCallbacks
    def add_dataset(self, dataset):
        try:
            self.dataset_queue.put(dataset, block=False)
        except queue.Full:
            remove_ds = self.dataset_queue.get()
            self.remove_dataset(remove_ds)
            self.dataset_queue.put(dataset, block=False)
        labels = yield dataset.getLabels()
        for i, label in enumerate(labels):
            self.add_artist(label, dataset, i)

    @inlineCallbacks
    def remove_dataset(self, dataset):
        labels = yield dataset.getLabels()
        for label in labels:
            self.remove_artist(label)

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
    app = QtWidgets.QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    main = Graph_PyQtGraph('example', reactor)
    main.show()
    #sys.exit(app.exec_())
    reactor.run()
