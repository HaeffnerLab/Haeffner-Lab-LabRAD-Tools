from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from analysis.fitting import FitWrapper

class FitWindow(QtGui.QWidget):

    def __init__(self, dataset, index):
        super(FitWindow, self).__init__()
        self.dataset = dataset
        self.index = index
        self.fw = FitWrapper(dataset, index)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Fit: ' + str(self.dataset.dataset_name))
        mainLayout = QtGui.QVBoxLayout()

        self.model_select = QtGui.QComboBox(self)
        for model in self.fw.models:
            self.model_select.addItem(model)

        self.parameterTable = QtGui.QTableWidget()
        self.parameterTable.setColumnCount(4)

        self.fitButton = QtGui.QPushButton('Fit', self)

        self.model_select.activated.connect(self.onActivated)
        self.fw.setModel(self.model_select.currentText())
        self.setupParameterTable()

        mainLayout.addWidget(self.model_select)
        mainLayout.addWidget(self.parameterTable)
        mainLayout.addWidget(self.fitButton)
        self.setLayout(mainLayout)
        self.show()

    def setupParameterTable(self):

        self.parameterTable.clear()
        
        headerLabels = QtCore.QStringList(['Vary', 'Param', 'Manual', 'Fitted'])
        self.parameterTable.setHorizontalHeaderLabels(headerLabels)
        self.parameterTable.horizontalHeader().setStretchLastSection(True)

        params = self.fw.getParameters()
        self.parameterTable.setRowCount(len(params))
        for i,p in enumerate(params):
            vary_select = QtGui.QTableWidgetItem()
            label = QtGui.QLabel(p)
            manual_value = QtGui.QDoubleSpinBox()
            fitted_value = QtGui.QTableWidgetItem()
            
            vary_select.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            if self.fw.getVary(p):
                vary_select.setCheckState(QtCore.Qt.Checked)
            else:
                vary_select.setCheckState(QtCore.Qt.Unchecked)

            manual_value.setValue(0.0)
            fitted_value.setText(str(0.0003))
            self.parameterTable.setItem(i, 0, vary_select)
            self.parameterTable.setCellWidget(i, 1, label)
            self.parameterTable.setCellWidget(i, 2, manual_value)
            self.parameterTable.setItem(i, 3, fitted_value)

    def updateParametersToFitter(self):
        params = self.fw.getParameters()
        for i, p in enumerate(params):
            pass

    def onActivated(self):
        model = self.model_select.currentText()
        self.fw.setModel(model)
        self.setupParameterTable()
