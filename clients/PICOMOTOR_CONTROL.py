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

        # absolute position
        absolute = QtGui.QHBoxLayout()
        self.absolute_position = QtGui.QSpinBox()
        self.move_absolute_button = QtGui.QPushButton('Move')
        absolute.addStretch(1)
        absolute.addWidget(self.absolute_position)
        absolute.addWidget(self.move_absolute_button)

        # move forward or back by some number of steps
        updown = QtGui.QHBoxLayout()
        self.step_size = QtGui.QSpinBox()
        self.button_increase = QtGui.QPushButton('>')
        self.button_decrease = QtGui.QPushButton('<')
        updown.addStretch(1)
        updown.addWidget(self.step_size)
        updown.addWidget(self.button_decrease)
        updown.addWidget(self.button_increase)

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(absolute)
        vbox.addLayout(updown)
        #self.setGeometry(300, 300, 300, 150)
        self.setLayout(vbox)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = PICOMOTOR_AXIS()
    window.show()
    sys.exit(app.exec_())
