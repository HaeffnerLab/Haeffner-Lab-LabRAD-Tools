from PyQt4 import QtGui, QtCore
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
        self.plt = plt = pg.PlotItem()
        self.img_view = pg.ImageView(view = self.plt)
        plt.showAxis('top')
        plt.hideAxis('bottom')
        plt.setAspectLocked(True)
        layout.addWidget(self.img_view, 0, 0, 1, 6)
        self.img_view.getHistogramWidget().setHistogramRange(0, 1000)
        exposure_label = QtGui.QLabel("Exposure")
        exposure_label.setAlignment(QtCore.Qt.AlignRight| QtCore.Qt.AlignVCenter)
        self.exposureSpinBox = QtGui.QDoubleSpinBox()
        self.exposureSpinBox.setDecimals(3)
        self.exposureSpinBox.setSingleStep(0.001)
        self.exposureSpinBox.setMinimum(0.0)
        self.exposureSpinBox.setMaximum(10000.0)
        self.exposureSpinBox.setKeyboardTracking(False)
        self.exposureSpinBox.setSuffix(' s')      
        layout.addWidget(exposure_label, 1, 4,)
        layout.addWidget(self.exposureSpinBox, 1, 5)
        #EMCCD Gain
        emccd_label = QtGui.QLabel("EMCCD Gain")
        emccd_label.setAlignment(QtCore.Qt.AlignRight| QtCore.Qt.AlignVCenter)
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
        layout.addWidget(self.live_button, 1, 0)
        #set image region button
        self.set_image_region_button = QtGui.QPushButton("Set Image Region")
        layout.addWidget(self.set_image_region_button, 2, 0)
        #controlling the display buttons
        self.view_all_button = QtGui.QPushButton("View All")
        layout.addWidget(self.view_all_button, 1, 1)
        self.auto_levels_button = QtGui.QPushButton("Auto Levels")
        layout.addWidget(self.auto_levels_button, 2, 1)
        #display mode buttons
        self.trigger_mode = QtGui.QLineEdit()
        self.acquisition_mode = QtGui.QLineEdit()
        self.trigger_mode.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.acquisition_mode.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.trigger_mode.setReadOnly(True)
        self.acquisition_mode.setReadOnly(True)
        label = QtGui.QLabel("Trigger Mode")
        label.setAlignment(QtCore.Qt.AlignRight| QtCore.Qt.AlignVCenter)
        layout.addWidget(label, 1, 2)
        label = QtGui.QLabel("Acquisition Mode")
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        layout.addWidget(label, 2, 2)
        layout.addWidget(self.trigger_mode, 1, 3)
        layout.addWidget(self.acquisition_mode, 2, 3)
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
        self.set_image_region_button.clicked.connect(self.on_set_image_region)
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        exposure = yield self.server.getExposureTime(None)
        self.exposureSpinBox.setValue(exposure['s'])     
        self.exposureSpinBox.valueChanged.connect(self.on_new_exposure)
        gain = yield self.server.getEMCCDGain(None)
        self.emccdSpinBox.setValue(gain)
        trigger_mode = yield self.server.getTriggerMode(None)
        self.trigger_mode.setText(trigger_mode)
        acquisition_mode = yield self.server.getAcquisitionMode(None)
        self.acquisition_mode.setText(acquisition_mode)
        self.emccdSpinBox.valueChanged.connect(self.on_new_gain)
        self.live_button.clicked.connect(self.on_live_button)
        self.auto_levels_button.clicked.connect(self.on_auto_levels_button)
        self.view_all_button.clicked.connect(self.on_auto_range_button)
    
    def on_set_image_region(self, checked):
        #displays a non-modal dialog
        dialog = image_region_selection_dialog(self, self.server)
        one = dialog.open()
        two = dialog.show()
        three = dialog.raise_()
        
    def on_auto_levels_button(self, checked):
        self.img_view.autoLevels()
     
    def on_auto_range_button(self, checked):
        self.img_view.autoRange()
     
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
    
    def set_trigger_mode(self, mode):
        self.trigger_mode.setText(mode)
    
    def set_acquisition_mode(self, mode):
        self.acquisition_mode.setText(mode)
     
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
            yield self.server.setTriggerMode(None, 'Internal')
            yield self.server.setAcquisitionMode(None, 'Run till abort')
            yield self.server.startAcquisition(None)
            self.binx, self.biny, self.startx, self.stopx, self.starty, self.stopy = yield self.server.getImageRegion(None)
            self.pixels_x = (self.stopx - self.startx + 1) / self.binx
            self.pixels_y = (self.stopy - self.starty + 1) / self.biny
            yield self.server.waitForAcquisition(None)
            self.live_update_loop.start(0)
        else:
            yield self.live_update_loop.stop()
            yield self.server.abortAcquisition(None)
     
    @inlineCallbacks
    def live_update(self):
        data = yield self.server.getMostRecentImage(None)
        image_data = np.reshape(data, (self.pixels_y, self.pixels_x))
        self.img_view.setImage(image_data.transpose(), autoRange = False, autoLevels = False, pos = [self.startx, self.starty], scale = [self.binx,self.biny], autoHistogramRange = False)
     
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
    
class image_region_selection_dialog(QtGui.QDialog):
    def __init__(self, parent, server):
        super(image_region_selection_dialog, self).__init__(parent)
        self.server = server
        self.parent = parent
        self.setWindowTitle("Select Region")
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.setupLayout()
    
    def sizeHint(self):
        return QtCore.QSize(300, 120)    
        
    @inlineCallbacks
    def set_image_region(self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver):
        yield self.server.set_image_region(bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
    
    @inlineCallbacks
    def setupLayout(self):
        self.hor_max, self.ver_max =  yield self.server.get_detector_dimensions(None)
        self.hor_min, self.ver_min = [1, 1]
        cur_bin_hor, cur_bin_ver, cur_start_hor, cur_stop_hor, cur_start_ver, cur_stop_ver = yield self.server.getImageRegion(None)
        layout = QtGui.QGridLayout()
        default_button = QtGui.QPushButton("Default")
        start_label = QtGui.QLabel("Start")
        stop_label = QtGui.QLabel("Stop")
        bin_label = QtGui.QLabel("Bin")
        hor_label = QtGui.QLabel("Horizontal")
        ver_label = QtGui.QLabel("Vertical")
        self.start_hor = QtGui.QSpinBox()
        self.stop_hor = QtGui.QSpinBox()
        self.bin_hor = QtGui.QSpinBox()
        for button in [self.start_hor, self.stop_hor, self.bin_hor]:
            button.setRange(self.hor_min, self.hor_max)
        self.start_hor.setValue(cur_start_hor)
        self.stop_hor.setValue(cur_stop_hor)
        self.bin_hor.setValue(cur_bin_hor)
        self.start_ver = QtGui.QSpinBox()
        self.stop_ver = QtGui.QSpinBox()
        self.bin_ver = QtGui.QSpinBox()
        for button in [self.start_ver, self.stop_ver, self.bin_ver]:
            button.setRange(self.ver_min, self.ver_max)
        self.start_ver.setValue(cur_start_ver)
        self.stop_ver.setValue(cur_stop_ver)
        self.bin_ver.setValue(cur_bin_ver)
        layout.addWidget(default_button, 0, 0)
        layout.addWidget(start_label, 0, 1)
        layout.addWidget(stop_label, 0, 2)
        layout.addWidget(bin_label, 0, 3)
        layout.addWidget(hor_label, 1, 0)
        layout.addWidget(self.start_hor, 1, 1)
        layout.addWidget(self.stop_hor, 1, 2)
        layout.addWidget(self.bin_hor, 1, 3)
        layout.addWidget(ver_label, 2, 0)
        layout.addWidget(self.start_ver, 2, 1)
        layout.addWidget(self.stop_ver, 2, 2)
        layout.addWidget(self.bin_ver, 2, 3)
        submit_button = QtGui.QPushButton("Submit")
        layout.addWidget(submit_button, 3, 0, 1, 2)
        cancel_button = QtGui.QPushButton("Cancel")
        layout.addWidget(cancel_button, 3, 2, 1, 2)
        default_button.clicked.connect(self.on_default)
        submit_button.clicked.connect(self.on_submit)
        cancel_button.clicked.connect(self.on_cancel)
        self.setLayout(layout)
    
    def on_default(self, clicked):
        self.bin_hor.setValue(1)
        self.bin_ver.setValue(1)
        self.start_hor.setValue(self.hor_min)
        self.stop_hor.setValue(self.hor_max)
        self.start_ver.setValue(self.ver_min)
        self.stop_ver.setValue(self.ver_max)
    
    @inlineCallbacks
    def on_submit(self, clicked):
        bin_hor = self.bin_hor.value()
        bin_ver = self.bin_ver.value()
        start_hor = self.start_hor.value()
        stop_hor = self.stop_hor.value()
        start_ver = self.start_ver.value()
        stop_ver = self.stop_ver.value()
        yield self.do_submit(bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
    
    @inlineCallbacks
    def do_submit(self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver):
        if self.parent.live_update_loop.running:
            yield self.parent.on_live_button(False)
            try:
                yield self.server.setImageRegion(None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
            except Exception as e:
                yield self.parent.on_live_button(True)
            else:
                yield self.parent.on_live_button(True)
                self.close()
        else:
            try:
                yield self.server.setImageRegion(None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
            except Exception as e:
                pass
            else:
                self.close() 
        
    def on_cancel(self, clicked):
        self.close()