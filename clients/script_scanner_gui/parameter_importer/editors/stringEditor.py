from PyQt4 import QtGui, QtCore, uic
import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"selection.ui")
base, form = uic.loadUiType(path)

class StringEditor(base, form):
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)

    def guess(self):
        '''
        Nothing to guess
        '''
        pass

    def full_info(self):
        text = self.uiInput.toPlainText()
        text = str(text)
        full_info = ('string', text)
        return full_info        
