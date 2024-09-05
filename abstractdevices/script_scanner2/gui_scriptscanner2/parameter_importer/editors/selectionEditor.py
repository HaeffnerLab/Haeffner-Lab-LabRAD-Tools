from PyQt5 import QtCore, uic
import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"selection.ui")
base, form = uic.loadUiType(path)

class SelectionEditor(base, form):
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

        selections = []
        for selection in text.split(','):
            selections.append( selection.strip() )
            
        full_info = ('selection_simple', (selections[0], selections))
        return full_info        
