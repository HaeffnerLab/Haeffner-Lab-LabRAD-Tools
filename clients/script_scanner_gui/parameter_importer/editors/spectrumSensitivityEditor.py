from PyQt4 import QtGui, QtCore

class SpectrumSensitivityEditor(QtGui.QWidget):
    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.parent = parent
        self.setupUi()
    
    def setupUi(self):
        
        label = QtGui.QLabel('Spectrum sensitivity')
        layout = QtGui.QHBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

    def guess(self):
        pass

    def full_info(self):
        
        from labrad.units import WithUnit as U

        full_info = ('spectrum_sensitivity',(U(40.0,'kHz'),U(2.0,'kHz'),
                                 U(500.0,'us'), U(-24.0,'dBm')))
        
        return full_info
