from PyQt4 import QtCore, uic

class sequence_widget(QtGui.QWidget):
    def __init__(self, name, scannable_parameters):
        super(sequence_widget, self).__init__()
        
        

class scan_widget(QtGui.QWidget):

    def __init__(self, reactor, parent):
        super(scan_widget, self).__init__()
        self.parent = parent
        self.reactor = reactor
        self.setupLayout()
        self.widgets = {} # dictionary of widgets to show

    def setupLayout(self):
        pass

    def buildSequenceWidget(self, experiment, params):
        
        
