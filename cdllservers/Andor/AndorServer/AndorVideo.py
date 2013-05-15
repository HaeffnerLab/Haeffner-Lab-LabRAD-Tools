from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
import numpy as np
import pyqtgraph as pg

class AndorVideo(QtGui.QWidget):
    def __init__(self, server):
        super(AndorVideo, self).__init__()
        from labrad.units import WithUnit
        self.WithUnit = WithUnit
        self.server = server
        self.setup_layout()
        self.live_update_loop = LoopingCall(self.live_update)
        self.connect_layout()
        
    def setup_layout(self):
        self.setWindowTitle("Andor")
        #layout
        layout = QtGui.QGridLayout()
        #make a plot item with axes insdide graphicsview
        graphics_view = pg.GraphicsView()
        self.plt = plt = pg.PlotItem()
        #replace the view in the plotitem with an ImageView
        self.img_view = pg.ImageView(view=plt)
        graphics_view.setCentralItem(plt)
        #customize plotitem
        plt.showAxis('top')
        plt.hideAxis('bottom')
        plt.setAspectLocked(True)
        layout.addWidget(graphics_view, 0, 0, 1, 5)
        #histogram with the color bar
        w = pg.HistogramLUTWidget()
        w.setImageItem(self.img_view.getImageItem())
        w.setHistogramRange(0, 1000)
        layout.addWidget(w, 0, 5)
        exposure_label = QtGui.QLabel("Exposure")
        self.exposureSpinBox = QtGui.QDoubleSpinBox()
        self.exposureSpinBox.setSingleStep(0.001)
        self.exposureSpinBox.setMinimum(0.0)
        self.exposureSpinBox.setMaximum(10000.0)
        self.exposureSpinBox.setKeyboardTracking(False)
        self.exposureSpinBox.setSuffix(' s')      
        layout.addWidget(exposure_label, 1, 4,)
        layout.addWidget(self.exposureSpinBox, 1, 5)
        #EMCCD Gain
        emccd_label = QtGui.QLabel("EMCCD Gain")
        self.emccdSpinBox = QtGui.QSpinBox()
        self.emccdSpinBox.setSingleStep(1)  
        self.emccdSpinBox.setMinimum(0)
        self.emccdSpinBox.setMaximum(255)
        self.emccdSpinBox.setKeyboardTracking(False)
        layout.addWidget(emccd_label, 2, 4,)
        layout.addWidget(self.emccdSpinBox, 2, 5)
        #Live Video Button
        self.live_button = QtGui.QPushButton("Live Video")
        self.live_button.setCheckable(True)
        layout.addWidget(self.live_button, 2, 0)
        #add lines for the cross
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        plt.addItem(self.vLine, ignoreBounds=True)
        plt.addItem(self.hLine, ignoreBounds=True)
        #set the layout and show
        self.setLayout(layout)
        self.show()
    
    def mouse_clicked(self, event):
        '''
        draws the cross at the position of a double click
        '''
        pos = event.pos()
        if self.plt.sceneBoundingRect().contains(pos) and event.double():
            #only on double clicks within bounds
            mousePoint = self.plt.vb.mapToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
    
    @inlineCallbacks
    def connect_layout(self):
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        exposure = yield self.server.getExposureTime(None)
        self.exposureSpinBox.setValue(exposure['s'])     
        self.exposureSpinBox.valueChanged.connect(self.on_new_exposure)
        gain = yield self.server.getEMCCDGain(None)
        self.emccdSpinBox.setValue(gain)
        self.emccdSpinBox.valueChanged.connect(self.on_new_gain)
        self.live_button.clicked.connect(self.on_live_button)
    
    @inlineCallbacks
    def on_new_exposure(self, exposure):
        if self.live_update_loop.running:
            yield self.on_live_button(False)
            yield self.server.setExposureTime(None, self.WithUnit(exposure,'s'))
            yield self.on_live_button(True)
        else:
            yield self.server.setExposureTime(None, self.WithUnit(exposure,'s'))
    
    def set_exposure(self, exposure):
        self.exposureSpinBox.blockSignals(True)
        self.exposureSpinBox.setValue(exposure)
        self.exposureSpinBox.blockSignals(False)
    
    @inlineCallbacks
    def on_new_gain(self, gain):
        yield self.server.setEMCCDGain(None, gain)
    
    def set_gain(self, gain):
        self.emccdSpinBox.blockSignals(True)
        self.emccdSpinBox.setValue(gain)
        self.emccdSpinBox.blockSignals(False)
    
    @inlineCallbacks
    def on_live_button(self, checked):
        if checked:
            yield self.server.setAcquisitionMode(None, 'Run till abort')
            yield self.server.startAcquisition(None)
            binx,biny, startx, stopx, starty, stopy = yield self.server.getImageRegion(None)
            self.pixels_x = (stopx - startx + 1) / binx
            self.pixels_y = (stopy - starty + 1) / biny
            yield self.server.waitForAcquisition(None)
            self.live_update_loop.start(0)
        else:
            yield self.live_update_loop.stop()
            yield self.server.abortAcquisition(None)
    
    @inlineCallbacks
    def live_update(self):
        data = yield self.server.getMostRecentImage(None)
        image_data = np.reshape(data, (self.pixels_y, self.pixels_x))
        self.img_view.setImage(image_data.transpose(), autoRange = False, autoLevels = False)
    
    @inlineCallbacks
    def start_live_display(self):
        self.live_button.setChecked(True)
        yield self.on_live_button(True)
    
    @inlineCallbacks
    def stop_live_display(self):
        self.live_button.setChecked(False)
        yield self.on_live_button(False)
    
    @property
    def live_update_running(self):
        return self.live_update_loop.running

    def closeEvent(self, event):
        self.server.stop()