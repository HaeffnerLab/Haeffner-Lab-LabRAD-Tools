from PyQt4 import QtGui

class ActiveExperimentsListWidget(QtGui.QListWidget):
    def __init__(self, parent):
        QtGui.QListWidget.__init__(self)
        self.parent = parent
        self.activeExperiments = {} #dictionary in the form {'experiment name':qlabelwidget}
        self.currentItemChanged.connect(self.on_change)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        
    def on_change(self, current, previous):
        if current is not None:
            experiment = [key for key in self.activeExperiments.keys() if self.activeExperiments[key] == current][0]
            experiment = list(experiment)
            self.parent.setupStatusWidget(experiment)
    
    def addExperiment(self, experiment):
        key =  tuple(experiment)
        label = key[-1]
        widget_item = QtGui.QListWidgetItem(label)
        self.activeExperiments[key] = widget_item
        self.addItem(widget_item)
        
    def removeExperiment(self, experiment):
        print 'trying to remove experiment does this happen twice?', experiment
        key =  tuple(experiment)
        if key in self.activeExperiments.keys(): 
            item = self.activeExperiments[key]
            row = self.row(item)
            list_widget = self.takeItem(row)
            del(list_widget)
            del(self.activeExperiments[key])