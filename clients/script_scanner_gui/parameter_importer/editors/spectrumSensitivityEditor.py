from PyQt5 import QtCore, QtGui, QtWidgets

class SpectrumSensitivityEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(QtWidgets.QWidget, self).__init__(parent)
        self.parent = parent
        self.setupUi()
    
    def setupUi(self):
        
        label = QtWidgets.QLabel('Spectrum sensitivity')
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

    def guess(self):
        pass

    def full_info(self):
        
        from labrad.units import WithUnit as U

        full_info = ('spectrum_sensitivity',(U(40.0,'kHz'),U(2.0,'kHz'),
                                 U(500.0,'us'), U(-24.0,'dBm')))
        
        return full_info
