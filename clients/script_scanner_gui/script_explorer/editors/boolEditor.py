from PyQt4 import QtGui, QtCore, uic

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
        There's no guessin' a boolean
        '''
        pass
