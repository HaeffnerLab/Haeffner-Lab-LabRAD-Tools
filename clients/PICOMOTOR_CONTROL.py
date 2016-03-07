'''
Control for Newport picomotor stages
'''
from connection import connection
from twisted.internet.defer import inlineCallbacks, returnValue
from PyQt4 import QtGui
from PyQt4 import QtCore

class PICOMOTOR_AXIS(QtGui.QWidget):
    
    def __init__(self, name, axis, reactor):
        QtGui.QWidget.__init__(self)
        self.reactor = reactor
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        #self.context = context
        #self.cxn = cxn
        self.axis = axis
        self.initUI(name)

    def initUI(self, name):

        title = QtGui.QLabel(name + '\t(%d)' % self.axis)
        title.setAlignment(QtCore.Qt.AlignCenter)
        # absolute position
        absolute = QtGui.QHBoxLayout()
        self.absolute_position = QtGui.QSpinBox()
        self.absolute_position.setRange(-100000, 100000)
        self.move_absolute_button = QtGui.QPushButton('Move')
        absolute.addStretch(1)
        absolute.addWidget(self.absolute_position)
        absolute.addWidget(self.move_absolute_button)

        # move forward or back by some number of steps
        updown = QtGui.QHBoxLayout()
        self.step_size = QtGui.QSpinBox()
        self.step_size.setRange(0, 10000)
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

        self.button_increase.clicked.connect(self.move_pos)
        self.button_decrease.clicked.connect(self.move_neg)
        self.move_absolute_button.clicked.connect(self.move_absolute)
        self.setLayout(vbox)

    @inlineCallbacks
    def move_pos(self, x):
        move = self.step_size.value()
        print move
        yield None

    @inlineCallbacks
    def move_neg(self, x):
        move = -self.step_size.value()
        print move
        yield None
    
    @inlineCallbacks
    def move_absolute(self, x):
        move = self.absolute_position.value()
        print move
        yield None

    def closeEvent(self, x):
        self.reactor.stop()

class PICOMOTOR_CONTROL(QtGui.QWidget):

    def __init__(self, reactor):
        QtGui.QWidget.__init__(self)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.initUI()
    
    def initUI(self):
        grid = QtGui.QGridLayout()
        reactor = self.reactor
        axes = [PICOMOTOR_AXIS('local_horiz', 1, reactor),
                PICOMOTOR_AXIS('local_vert', 2, reactor),
                PICOMOTOR_AXIS('global_horiz', 3, reactor),
                PICOMOTOR_AXIS('global_vert', 4, reactor)]

        grid.addWidget(axes[0], 1,1)
        grid.addWidget(axes[1], 1,2)
        grid.addWidget(axes[2], 2,1)
        grid.addWidget(axes[3], 2,2)
        self.setLayout(grid)

    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == '__main__':

    app = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    window = PICOMOTOR_CONTROL(reactor)
    window.show()
    reactor.run()
