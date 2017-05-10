import sys
from tree_view.Controllers import ParametersEditor
from PyQt4 import QtCore, QtGui, uic

class ScanItem(QtGui.QWidget):
    """ Item for parameter scanning """
    def __init__(self, p, parent = None):
        super(ScanItem, self).__init__(parent)
        parameter, minim, maxim, steps, unit = p
        self.parameter = parameter
        self.makeLayout(p)

    def makeLayout(self, p):
        parameter, minim, maxim, steps, unit = p
        layout = QtGui.QHBoxLayout()

        self.select = QtGui.QCheckBox()
        layout.addWidget(self.select)
        label = QtGui.QLabel(parameter)
        layout.addWidget(label)
        self.minim = QtGui.QDoubleSpinBox()
        self.maxim = QtGui.QDoubleSpinBox()
        self.steps = QtGui.QSpinBox()
        layout.addWidget(self.minim)
        layout.addWidget(self.maxim)
        layout.addWidget(self.steps)
        unitLabel = QtGui.QLabel(unit)
        layout.addWidget(unitLabel)
        self.setLayout(layout)
        
class sequence_widget(QtGui.QWidget):
    def __init__(self, params, editor):
        super(sequence_widget, self).__init__()
        self.parameters = {}
        self.makeLayout(params, editor)

    def makeLayout(self, params, editor):
        layout = QtGui.QVBoxLayout()
        for par, x in params:
            minim, maxim, steps, unit = x
            p = (par, minim, maxim, steps, unit)
            self.parameters[par] = ScanItem(p)
            layout.addWidget(self.parameters[par])
        layout.addWidget(editor)
        self.setLayout(layout)
        
class scan_widget(QtGui.QStackedWidget):

    def __init__(self, reactor, parent):
        super(scan_widget, self).__init__()
        self.parent = parent
        self.setupLayout()
        self.reactor = reactor
        self.ParametersEditor = ParametersEditor(self.reactor)
        self.widgets = {} # dictionary of widgets to show

    def setupLayout(self):
        pass

    def buildSequenceWidget(self, experiment, params):
        '''
        params = [par, ( min, max, steps, unit)]
        '''
        sw = sequence_widget(params, self.ParametersEditor)
        self.addWidget(sw)
        self.widgets[experiment] = sw
        self.setCurrentWidget(sw)

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    params = [(0, 6, 2, 'kHz'), ('p2', 0, 8, 2, 'us')]
    #icon = sequence_widget(params)
    icon = scan_widget(None)
    icon.buildSequenceWidget('exp', params)
    icon.show()
    app.exec_()
