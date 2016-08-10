from PyQt4 import QtGui, QtCore
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred
from analysis.fitting import FitWrapper

class RowInfo():
    '''
    Container for the widgets with
    each row in the parameters table
    '''
    def __init__(self, vary, manual_value, fitted_value):
        self.vary_select = vary
        self.manual_value = manual_value
        self.fitted_value = fitted_value

class FitWindow(QtGui.QWidget):

    def __init__(self, dataset, index, parent):
        super(FitWindow, self).__init__()
        self.dataset = dataset
        self.index = index
        self.parent = parent
        self.fw = FitWrapper(dataset, index)
        self.row_info_dict = {}
        self.ident = 'Fit: ' + str(self.dataset.dataset_name)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.ident)
        mainLayout = QtGui.QVBoxLayout()

        self.model_select = QtGui.QComboBox(self)
        for model in self.fw.models:
            self.model_select.addItem(model)

        self.parameterTable = QtGui.QTableWidget()
        self.parameterTable.setColumnCount(4)

        self.fitButton = QtGui.QPushButton('Fit', self)

        self.fw.setModel(self.model_select.currentText())

        mainLayout.addWidget(self.model_select)
        mainLayout.addWidget(self.parameterTable)
        mainLayout.addWidget(self.fitButton)
        
        self.model_select.activated.connect(self.onActivated)
        self.fitButton.clicked.connect(self.onClick)

        self.setupParameterTable()
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

            self.row_info_dict[p] = RowInfo(vary_select, manual_value, fitted_value)

            vary_select.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            if self.fw.getVary(p):
                vary_select.setCheckState(QtCore.Qt.Checked)
            else:
                vary_select.setCheckState(QtCore.Qt.Unchecked)

            manualValue = self.fw.getManualValue(p)
            manual_value.setValue(manualValue)

            fittedValue = self.fw.getFittedValue(p)
            fitted_value.setText(str(fittedValue))
            self.parameterTable.setItem(i, 0, vary_select)
            self.parameterTable.setCellWidget(i, 1, label)
            self.parameterTable.setCellWidget(i, 2, manual_value)
            self.parameterTable.setItem(i, 3, fitted_value)            

    def updateParametersToFitter(self):
        params = self.fw.getParameters()
        for p in params:
            row = self.row_info_dict[p]
            vary = row.vary_select.checkState()
            manual_value = row.manual_value.value()
            if vary:
                self.fw.setVary(p, True)
            else:
                self.fw.setVary(p, False)
            self.fw.setManualValue(p, manual_value)

    def updateParametersFromFitter(self):
        params = self.fw.getParameters()
        for p in params:
            row = self.row_info_dict[p]
            fitted_value = self.fw.getFittedValue(p)
            print fitted_value
            row.fitted_value.setText( str(fitted_value) )

    def plotFit(self):
        '''
        Plot the fitted parameters.
        We need to wrap the data in a dataset
        object to use add_artist in GraphWidget
        '''

        class dataset():
            def __init__(self, data):
                self.data = data
                self.updateCounter = 1
        data = self.fw.evaluateFittedParameters()
        ds = dataset(data)
        try:
            # remove the previous fit
            self.parent.parent.remove_artist(self.ident)
            self.parent.parent.add_artist(self.ident, ds, 0, no_points = True)
        except:
            self.parent.parent.add_artist(self.ident, ds, 0, no_points = True)
        

    def onActivated(self):
        '''
        Run when model is changed.
        Reset row_info_dict each
        time the model is changed.
        '''
        model = self.model_select.currentText()
        self.fw.setModel(model)
        self.row_info_dict = {}
        self.setupParameterTable()

    def onClick(self):
        '''
        Send table parameters to fitter,
        perform fit, and then update
        paramter table with the results
        '''

        self.updateParametersToFitter()
        self.fw.doFit()
        self.updateParametersFromFitter()
        self.plotFit()

    def closeEvent(self, event):
        self.parent.parent.remove_artist(self.ident)
