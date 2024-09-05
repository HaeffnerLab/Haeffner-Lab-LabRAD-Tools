from PyQt5 import QtCore, uic
import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"parameter.ui")

base, form = uic.loadUiType(path)

class ParameterEditor(base, form):

    units = [
        '',
        'MHz',
        'kHz',
        'dBm',
        'us',
        'ms',
        's',
        ]

    def __init__(self, parent = None):
        super(base, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)

        for u in self.units:
            self.uiUnit.addItem(u)

    def guess(self):
        '''
        Try to guess parameters
        '''

        param = self.parent.current_parameter
        if param is None:
            param = ''

        if 'frequency' in param:
            index = self.uiUnit.findText('MHz')
            self.uiUnit.setCurrentIndex(index)

        elif 'amplitude' in param:
            index = self.uiUnit.findText('dBm')
            self.uiUnit.setCurrentIndex(index)
        
        elif 'duration' in param:
            index = self.uiUnit.findText('us')
            self.uiUnit.setCurrentIndex(index)

        else:
            index = self.uiUnit.findText('')
            self.uiUnit.setCurrentIndex(index)

        self.uiMin.setValue(-100.)
        self.uiMax.setValue(100)

    def full_info(self):
        '''
        Full info for creating parameter
        '''
        from labrad.units import WithUnit as U
        unit = str(self.uiUnit.currentText())
        minim = self.uiMin.value()
        maxim = self.uiMax.value()
        value = (maxim + minim)/2.0
        full_info = ('parameter', [U(minim, unit), U(maxim, unit), U(value, unit)])
        return full_info
