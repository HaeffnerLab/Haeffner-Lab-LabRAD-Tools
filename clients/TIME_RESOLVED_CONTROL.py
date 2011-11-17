import sys
import os
from PyQt4 import QtGui
from PyQt4 import QtCore,uic
import labrad
import time

class TIME_RESOLVED_CONTROL(QtGui.QWidget):
    def __init__(self, server, parent=None):
        QtGui.QWidget.__init__(self, parent)
        basepath = os.environ.get('LABRADPATH',None)
        if not basepath:
            raise Exception('Please set your LABRADPATH environment variable')
        path = os.path.join(basepath,'lattice/clients/qtui/timeresolvedfrontend.ui')
        uic.loadUi(path,self)
        self.server = server
        #connect functions
        self.pushButton.toggled.connect(self.on_toggled)
        isreceiving = self.server.isreceiving()
        self.setText(self.pushButton)
        self.pushButton.setChecked(isreceiving)
        dataset = self.server.currentdataset()
        self.lineEdit.setText(dataset)
        self.newSet.clicked.connect(self.onNewSet)
        
    def on_toggled(self, state):
        if state:
            self.server.startreceiving()
        else:
            self.server.stopreceiving()
        self.setText(self.pushButton)
        
    def onNewSet(self):
        newset = self.server.newdataset()
        self.lineEdit.setText(newset)
    
    def setText(self, obj):
        state = obj.isChecked()
        if state:
            obj.setText('ON')
        else:
            obj.setText('OFF')            
            
if __name__=="__main__":
    cxn = labrad.connect()
    server = cxn.time_resolved_server
    app = QtGui.QApplication(sys.argv)
    icon = TIME_RESOLVED_CONTROL(server)
    icon.show()
    app.exec_()

 
