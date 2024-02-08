import time
import numpy as np
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread
from PyQt5 import QtCore, QtGui, QtWidgets

class Keithly6487Client(QtWidgets.QWidget):
    def __init__(self,reactor, parent=None):
        QtWidgets.QWidget.__init__(self)
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.server = self.cxn.lattice_imaging_keithly_6487
        self.setupWidget()
        
    def setupWidget(self):
        self.setGeometry(300, 300, 250, 150)
        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(5)
        
        measureButton = QtWidgets.QPushButton("Measure", self)
        measureButton.setGeometry(QtCore.QRect(0, 0, 30, 30))
        measureButton.clicked.connect(self.measure)

        dataPointsLabel = QtWidgets.QLabel('Data Points: ')
        
        self.dataPointsSpinBox = QtWidgets.QSpinBox()
        self.dataPointsSpinBox.setRange(0, 10000000)
        self.dataPointsSpinBox.setValue(1)
        self.dataPointsSpinBox.setSingleStep(1)
        
        iterationsLabel = QtWidgets.QLabel('Iterations: ')
        
        self.iterationsSpinBox = QtWidgets.QSpinBox()
        self.iterationsSpinBox.setRange(0, 10000000)
        self.iterationsSpinBox.setValue(1)
        self.iterationsSpinBox.setSingleStep(1)

        intervalLabel = QtWidgets.QLabel('Interval (sec): ')
        
        self.intervalDoubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.intervalDoubleSpinBox.setRange(.25, 1000)
        self.intervalDoubleSpinBox.setValue(1)
        self.intervalDoubleSpinBox.setSingleStep(1)


        self.grid.addWidget(measureButton, 0, 0, QtCore.Qt.AlignCenter)
        self.grid.addWidget(dataPointsLabel, 0, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.dataPointsSpinBox, 0, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(iterationsLabel, 1, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.iterationsSpinBox, 1, 2, QtCore.Qt.AlignCenter)
        self.grid.addWidget(intervalLabel, 2, 1, QtCore.Qt.AlignCenter)
        self.grid.addWidget(self.intervalDoubleSpinBox, 2, 2, QtCore.Qt.AlignCenter)

        self.setLayout(self.grid)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
        self.show()

    @inlineCallbacks    
    def measure(self, evt = None):
        print('Starting Measurement')
        yield self.cxn.data_vault.cd(['', 'QuickMeasurements', 'Keithly 6487 Current Monitoring', str(time.strftime("%Y%b%d",time.localtime()))], True)
        yield self.cxn.data_vault.new('Current',[('Time', 'sec')],[('Current','Amp','Arb')] )
        yield self.cxn.data_vault.add_parameter('plotLive', True)
        
        for i in range(self.iterationsSpinBox.value()):
            print('iteration: ', i + 1)
            data = yield self.server.measure_current(self.dataPointsSpinBox.value())
            Data = [data]
            print(Data)
#            Data2 = [Data[0], Data[1]]
#            print Data2
            yield self.cxn.data_vault.add(Data)
            yield deferToThread(time.sleep, self.intervalDoubleSpinBox.value())
    
    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtWidgets.QApplication( [] )
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    keithly6487Client = Keithly6487Client(reactor)
    reactor.run()
