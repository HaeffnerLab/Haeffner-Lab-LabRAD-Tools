from PyQt5 import QtCore, uic
import os
basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"sidebandSelectionEditor.ui")
base, form = uic.loadUiType(path)

class SidebandSelectionEditor(base, form):
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.parent = parent
        self.setupUi(self)

    def guess(self):        
        self.uiRadial1.setValue(0)
        self.uiRadial2.setValue(0)
        self.uiAxial.setValue(0)
        self.uiMicromotion.setValue(0)

    def full_info(self):
        
        settings = [self.uiRadial1.value(),
                    self.uiRadial2.value(),
                    self.uiAxial.value(),
                    self.uiMicromotion.value()
                    ]

        full_info = ('sideband_selection', settings)
        return full_info
