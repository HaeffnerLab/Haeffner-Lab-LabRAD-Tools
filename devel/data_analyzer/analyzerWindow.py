from PyQt4 import QtGui, QtCore
# from twisted.internet.defer import inlineCallbacks
# from twisted.internet.task import LoopingCall
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg as FigureCanvas,NavigationToolbar2QTAgg as NavigationToolbar)

class AnalyzerWindow(QtGui.QWidget):
       
    def __init__(self, fitting_parameters, interface):
        super(AnalyzerWindow, self).__init__()
        self.create_layout(fitting_parameters)
        self.connect_layout()
        self.interface = interface
    
    def create_layout(self, fitting_parameters):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.fig.set_facecolor('w')
        self.fig.subplots_adjust(left=0.07, right=0.93, top=0.93, bottom=0.07)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        mpl_toolbar = NavigationToolbar(self.canvas, self)
        self.accept_button = QtGui.QPushButton('Accept')
        self.reject_button = QtGui.QPushButton('Reject')
        self.fit_button = QtGui.QPushButton("Fit")
        button_row = QtGui.QHBoxLayout()
        button_row.addWidget(self.accept_button)
        button_row.addWidget(self.reject_button)
        button_row.addWidget(self.fit_button)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(button_row)
        self.grid = parameterTable(fitting_parameters)
        vbox.addWidget(self.grid)
        self.setLayout(vbox)
        self.show()
    
    def connect_layout(self):
#         self.accept_button.pressed.connect(self.test)
        self.grid.onNewGuess.connect(self.onNewGuess)
#         self.grid.onNewGuess.connect(self.test, True)
    
    def onNewGuess(self):
        params = self.grid.get_manual_values()
        evalX, evalY = self.interface.evaluate_params(params)
        self.plot(evalX, evalY, 'g--')
    
    def plot(self, x, y, *args):
        self.axes.plot(x,y, *args)
        self.fig.canvas.draw()
    
    def get_manual_values(self):
        return self.grid.get_manual_values()
        
class parameterTable(QtGui.QTableWidget):
    
    onNewGuess = QtCore.pyqtSignal(bool)
    
    def __init__(self, fitting_parameters):
        super(parameterTable, self).__init__()
        #set columns
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(['Fit','Auto','Guess','Last Fit'])
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
            to_fit, auto_fit, manual_value, last_fit = fitting_parameters[parameter]
            cb_to_fit = QtGui.QCheckBox()
            cb_to_fit.setCheckable(True)
            cb_to_fit.setChecked(to_fit)
            self.setCellWidget(row,0, cb_to_fit)
            cb_auto_fit = QtGui.QCheckBox()
            cb_auto_fit.setCheckable(True)
            cb_auto_fit.setChecked(auto_fit)
            self.setCellWidget(row,1, cb_auto_fit)
            spin_manual = QtGui.QDoubleSpinBox()
            spin_manual.setRange(-10000000, 10000000)
            spin_manual.setDecimals(5)
            if manual_value is None: manual_value = last_fit
            spin_manual.setValue(manual_value)
            self.setCellWidget(row,2, spin_manual)
            spin_manual.valueChanged.connect(self.onNewGuess.emit, True)
            spin_result = QtGui.QDoubleSpinBox()
            spin_result.setRange(-10000000, 10000000)
            spin_result.setDecimals(5)
            spin_result.setReadOnly(True)
            spin_result.setValue(last_fit)
            spin_result.setAlignment(QtCore.Qt.AlignCenter)
            self.setCellWidget(row,3, spin_result)
        #set size policy and selection policy
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.Stretch)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
    
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