'''
Control for Newport picomotor stages
'''
from connection import connection
from twisted.internet.defer import inlineCallbacks, returnValue
from PyQt4 import QtGui
from PyQt4 import QtCore

class PICOMOTOR_AXIS(QtGui.QWidget):
    
    def __init__(self, name, axis):
        QtGui.QWidget.__init__(self)
        self.axis = axis
        self.initUI(name)

    def initUI(self, name):

        title = QtGui.QLabel(name + '\t(%d)' % self.axis)
        title.setAlignment(QtCore.Qt.AlignCenter)
        # absolute position
        absolute = QtGui.QHBoxLayout()
        self.absolute_position = QtGui.QLineEdit()
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
        vbox.addWidget(title)
        vbox.addLayout(absolute)
        vbox.addLayout(updown)
        #self.setGeometry(300, 300, 300, 150)
        self.setLayout(vbox)

class PICOMOTOR_CONTROL(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.initUI()
    
    def initUI(self):
        grid = QtGui.QGridLayout()
        
        axes = [PICOMOTOR_AXIS('local_horiz', 1),
                PICOMOTOR_AXIS('local_vert', 2),
                PICOMOTOR_AXIS('global_horiz', 3),
                PICOMOTOR_AXIS('global_vert', 4)]

        grid.addWidget(axes[0], 1,1)
        grid.addWidget(axes[1], 1,2)
        grid.addWidget(axes[2], 2,1)
        grid.addWidget(axes[3], 2,2)
        self.setLayout(grid)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    #window = PICOMOTOR_AXIS('local_horiz', 1)
    window = PICOMOTOR_CONTROL()
    window.show()
    sys.exit(app.exec_())
