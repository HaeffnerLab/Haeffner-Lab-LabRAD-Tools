from PyQt4 import QtGui, QtCore, uic

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
