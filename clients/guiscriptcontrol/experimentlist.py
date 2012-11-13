'''
Experiment List Widget
'''
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


class ExperimentListWidget(QtGui.QListWidget):

    def __init__(self, parent):
        QtGui.QListWidget.__init__(self)
        self.parent = parent
        self.path = []
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.MinimumExpanding)
        self.setMaximumWidth(425)

    
    @inlineCallbacks
    def populateList(self, path):
        self.clear()
        directories = yield self.parent.server.get_directory_names(path)
        self.addItem('..')
        for directory in directories:
            self.addItem(directory)
        
        self.sortItems()

        
    def mousePressEvent(self, event):
        """
        mouse clicks events
        """
        button = event.button()
        item = self.itemAt(event.x(), event.y())
        if item:
            if (item == self.item(0)):
                if (button == 1):
                    if (self.path == []):
                        pass
                    else:
                        self.path = self.path[:-1]
                        self.populateList(self.path)
            else:
                if (button == 1):
                    itemText = str(item.text())
                    self.handleMouseClick(itemText)
                    item.setSelected(True)
    
    @inlineCallbacks
    def handleMouseClick(self, itemText):
        newDirectories = yield self.parent.server.get_directory_names(self.path + [itemText])
        if (newDirectories == ['Semaphore']):
            self.parent.experimentParametersWidget.setupExperimentGrid(self.path + [itemText])
            self.parent.experimentParametersWidget.setupGlobalGrid(self.path + [itemText])
            self.parent.setupStatusWidget(self.path + [itemText])
        else:
            self.path = self.path + [itemText]
            self.populateList(self.path)
        



