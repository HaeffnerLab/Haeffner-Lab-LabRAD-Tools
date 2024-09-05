from PyQt5 import QtCore, uic

import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"bool.ui")

base, form = uic.loadUiType(path)

class BoolEditor(base, form):

    def __init__(self, parent = None):
        super(base, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)

    def guess(self):
        '''
        Ain't no guessin' a boolean
        '''
        pass

    def full_info(self):
        b = self.uiCheck.isChecked()
        full_info = ('bool', b)
        return full_info
