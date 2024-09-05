from PyQt5 import QtCore, uic
import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"selection.ui")
base, form = uic.loadUiType(path)

class LineSelectionEditor(base, form):
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)
        
        lines = ['S+1/2D+3/2',
                 'S-1/2D+1/2',
                 'carrier -1/2-5/2',
                 'carrier -1/2-1/2',
                 'S+1/2D-1/2',
                 'OP',
                 'S+1/2D+5/2',
                 'Right OP',
                 'S-1/2D-3/2',
                 'S+1/2D+1/2'
                 ]
        selections = '\n'.join(lines)
        self.uiInput.setText(selections)
        self.uiInput.setReadOnly(True)

    def guess(self):
        '''
        Nothing to guess
        '''
        pass

    def full_info(self):
        full_info = ('line_selection',('S-1/2D-5/2',[('S+1/2D+3/2','S+1/2D+3/2'),('S-1/2D+1/2','S-1/2D+1/2'),('S-1/2D-5/2','carrier -1/2-5/2'),('S-1/2D-1/2','carrier -1/2-1/2'),('S+1/2D-1/2','S+1/2D-1/2'),('S+1/2D-3/2','OP'),('S+1/2D+5/2','S+1/2D+5/2'),('S-1/2D+3/2','Right OP'),('S-1/2D-3/2','S-1/2D-3/2'),('S+1/2D+1/2','S+1/2D+1/2')]))
        return full_info
