from PyQt4 import QtCore, uic
import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","Views", "ParametersExplorer.ui")
base, form = uic.loadUiType(path)

class ParametersExplorer(base, form):

    def __init__(self, reactor, parent=None):
        super(base, self).__init__(parent)
        self.reactor = reactor
        self.setupUi(self)
        self._rootNode = None
        self.setup_model()
        self.connect_layout()
