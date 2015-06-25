#!/usr/bin/env python
# -*- coding: utf-8 -

from PyQt4 import QtGui, QtCore
# from twisted.internet.defer import inlineCallbacks
# from twisted.internet.task import LoopingCall
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg as FigureCanvas,NavigationToolbar2QTAgg as NavigationToolbar)

class AnalyzerWindow(QtGui.QWidget):
       
    def __init__(self, fitting_parameters, auto_accept, interface):
        super(AnalyzerWindow, self).__init__()
        self.create_layout(fitting_parameters, auto_accept)
        self.auto_accept = auto_accept
        if not auto_accept:
            self.connect_layout()
        self.interface = interface
        self.plotted_guess = None
        self.plotted_fit = None
        self.perform_customization()
        
    def perform_customization(self):
        '''
        can be subclassed to perform additional plot customization
        '''
        pass
    
    def create_layout(self, fitting_parameters, auto_accept):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.fig.set_facecolor('w')
        self.fig.subplots_adjust(left=0.07, right=0.93, top=0.93, bottom=0.07)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        mpl_toolbar = NavigationToolbar(self.canvas, self)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(mpl_toolbar)
        vbox.addWidget(self.canvas)
        if not auto_accept:
            self.accept_button = QtGui.QPushButton('Accept')
            self.reject_button = QtGui.QPushButton('Reject')
            self.fit_button = QtGui.QPushButton("Fit")
            button_row = QtGui.QHBoxLayout()
            button_row.addWidget(self.accept_button)
            button_row.addWidget(self.reject_button)
            button_row.addWidget(self.fit_button)
            vbox.addLayout(button_row)
            self.grid = parameterTable(fitting_parameters)
            vbox.addWidget(self.grid)
        self.setLayout(vbox)
        self.show()
    
    def connect_layout(self):
        self.grid.onNewGuess.connect(self.onNewGuess)
        self.fit_button.clicked.connect(self.on_fit)
        self.accept_button.clicked.connect(self.on_accept)
        self.reject_button.clicked.connect(self.on_reject)
    
    def on_accept(self):
        self.interface.setAccepted(True)
        self.close()
    
    def on_reject(self):
        self.interface.setAccepted(False)
        self.close()
    
    def on_fit(self):
        gui_values = self.grid.get_all_values()
        self.interface.refit(gui_values)
        if self.plotted_guess is not None:
            self.plotted_guess[0].set_alpha(0.5)
            self.fig.canvas.draw()
    
    def onNewGuess(self):
        if self.plotted_guess is not None:
            #remove the previous plotted guess
            self.plotted_guess.pop(0).remove()
        params = self.grid.get_manual_values()
        evalX, evalY = self.interface.evaluate_params(params)
        self.plotted_guess = self.plot(evalX, evalY, 'g--')
    
    def plot(self, x, y, *args):
        line = self.axes.plot(x,y, *args)
        self.fig.canvas.draw()
        return line
    
    def plotfit(self, x, y):
        if self.plotted_fit is not None:
            self.plotted_fit.pop(0).remove()
        self.plotted_fit = self.plot(x, y, 'r')
    
    def update_steps(self, values):
        if not self.auto_accept:
            for label, step in values:
                self.grid.updateStepSize(label, step)
    
    def set_last_fit(self, fitting_parameters):
        self.grid.set_last_fit(fitting_parameters)
        
class parameterTable(QtGui.QTableWidget):
    
    onNewGuess = QtCore.pyqtSignal(bool)
    
    def __init__(self, fitting_parameters):
        super(parameterTable, self).__init__()
        #set columns
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['Vary','Auto Guess','Guess Value','Last Fit'])
        #set rows
        self.setRowCount(len(fitting_parameters))
        labels = sorted(fitting_parameters.keys())
        self.setVerticalHeaderLabels(labels)
        #set font
        font =  self.horizontalHeader().font()
        font.setPointSize(12)
        self.setFont(font)
        #populate information
        for row, parameter in enumerate(labels):
            to_fit, auto_guess, manual_value, last_fit_value, stderror = fitting_parameters[parameter]
            cb_to_fit = QtGui.QCheckBox()
            cb_to_fit.setCheckable(True)
            cb_to_fit.setChecked(to_fit)
            self.setCellWidget(row,0, cb_to_fit)
            cb_auto_guess = QtGui.QCheckBox()
            cb_auto_guess.setCheckable(True)
            cb_auto_guess.setChecked(auto_guess)
            spin_manual = QtGui.QDoubleSpinBox()
            spin_manual.setKeyboardTracking(False)
            spin_manual.setRange(-10000000, 10000000)
            spin_manual.setDecimals(5)
            self.connect_disabling(cb_auto_guess, spin_manual)
            if manual_value is None: manual_value = last_fit_value
            spin_manual.setValue(manual_value)
            spin_manual.setSingleStep(1e-2)
            self.setCellWidget(row,1, cb_auto_guess)
            self.setCellWidget(row,2, spin_manual)
            spin_manual.valueChanged.connect(self.onNewGuess.emit, True)
            last_fit = QtGui.QLineEdit()
            last_fit.setReadOnly(True)
            last_fit.setText(u'{0:<10.5f} ± {1:.5f}'.format(last_fit_value, stderror))
            self.setCellWidget(row,3, last_fit)
        #set size policy and selection policy
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.Stretch)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
    
    def connect_disabling(self, cb, spin):
        if cb.isChecked():
            spin.setDisabled(True)
        def on_state_change(x):
            spin.setDisabled(bool(x))
        cb.stateChanged.connect(on_state_change)
    
    def updateStepSize(self, label, step):
        '''
        uses the value to set the step size of the given spin widget
        '''
        for row in range(self.rowCount()):
            row_label = str(self.verticalHeaderItem(row).text())
            if label == row_label:
                spin = self.cellWidget(row, 2)
                spin.setSingleStep(step)
        
    def sizeHint(self):
        oldSize = super(parameterTable, self).sizeHint()
        newheight = self.rowHeight(0) * self.rowCount() + self.horizontalHeader().height() + self.contentsMargins().top() +  self.contentsMargins().bottom()
        return QtCore.QSize(oldSize.width(),newheight)
    
    def get_manual_values(self):
        d = {}
        for row in range(self.rowCount()):
            label = str(self.verticalHeaderItem(row).text())
            value = self.cellWidget(row, 2).value()
            d[label] = value
        return d
    
    def get_all_values(self):
        d = {}
        for row in range(self.rowCount()):
            label = str(self.verticalHeaderItem(row).text())
            to_fit = self.cellWidget(row, 0).isChecked()
            auto_guess = self.cellWidget(row, 1).isChecked()
            value = self.cellWidget(row, 2).value()
            d[label] = (to_fit, auto_guess, value)
        return d
    
    def set_last_fit(self, fitting_parameters):
        for row in range(self.rowCount()):
            label = str(self.verticalHeaderItem(row).text())
            last_fit = self.cellWidget(row, 3)
            last_fit_value = fitting_parameters[label][3]
            stderror = fitting_parameters[label][4]
            last_fit.setText(u'{0:<10.5f} ± {1:.5f}'.format(last_fit_value, stderror))