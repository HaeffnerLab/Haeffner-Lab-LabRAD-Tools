'''
Queued Experiments List Widget
'''
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


class QueuedExperimentsListWidget(QtGui.QListWidget):

    def __init__(self, parent):
        QtGui.QListWidget.__init__(self)
        self.parent = parent
        self.experimentQueue = [] # list of experiment names
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.MinimumExpanding)
        self.setMaximumHeight(100)
        self.setMaximumWidth(425)
    
    def addExperiment(self, experiment):
        self.experimentQueue.append(experiment)
        self.populateList()
        
    def removeExperiment(self, experiment):
        try:
            self.experimentQueue.remove(experiment)
        except ValueError:
            # double signal?
            pass
        self.populateList()      

    def populateList(self):
        self.clear()
        for experiment in self.experimentQueue:
            self.addItem(experiment[-1])
        
    def mousePressEvent(self, event):
        """
        mouse clicks events
        """
        button = event.button()
        item = self.itemAt(event.x(), event.y())
        if item:
            if (button == 1):
                itemText = str(item.text())
                self.handleMouseClick(itemText)
                item.setSelected(True)
    
    def handleMouseClick(self, itemText):
        for experiment in self.experimentQueue:
            if (experiment[-1] == itemText):
                self.parent.setupStatusWidget(list(experiment))
