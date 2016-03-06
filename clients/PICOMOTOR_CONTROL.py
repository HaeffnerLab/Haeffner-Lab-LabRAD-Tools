'''
Control for Newport picomotor stages
'''
from connection import connection
from twisted.internet.defer import inlineCallbacks, returnValue
from PyQt4 import QtGui

class PICOMOTOR_AXIS(QtGui.QWidget):
    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.initUI()

    def initUI(self):

        hbox = QtGui.QHBoxLayout()
        self.button_increase = QtGui.QPushButton('>', self)
        self.button_decrease = QtGui.QPushButton('<', self)
        #self.button.clicked.connect(self.handleButton)
        hbox.addWidget(self.button_decrease)
        hbox.addWidget(self.button_decrease)
        self.setLayout(hbox)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = PICOMOTOR_AXIS()
    window.show()
    sys.exit(app.exec_())
