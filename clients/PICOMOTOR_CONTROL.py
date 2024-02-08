'''
Control for Newport picomotor stages
'''
from twisted.internet.defer import inlineCallbacks, returnValue
from .connection import connection
from PICOMOTOR_CONTROL_config import *
from PyQt4 import QtGui
from PyQt4 import QtCore

class PICOMOTOR_AXIS(QtGui.QWidget):
    
    def __init__(self, name, axis, reactor, cxn, context):
        QtGui.QWidget.__init__(self)
        self.reactor = reactor
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.context = context
        self.cxn = cxn
        self.axis = axis
        self.connect()
        self.initUI(name)

    @inlineCallbacks
    def connect(self):
        self.server = yield self.cxn.get_server('PicomotorServer')

    def initUI(self, name):
        title = QtGui.QLabel(name + '\t(%d)' % self.axis)
        title.setAlignment(QtCore.Qt.AlignCenter)

        # position label
        self.absolute_position_label = QtGui.QLabel('current:   ')

        # absolute position
        absolute = QtGui.QHBoxLayout()
        self.absolute_position_spin = QtGui.QSpinBox()
        self.absolute_position_spin.setRange(-100000, 100000)
        self.move_absolute_button = QtGui.QPushButton('Move')
        absolute.addStretch(1)
        absolute.addWidget(self.absolute_position_spin)
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
        vbox.addWidget(self.absolute_position_label)
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
        yield self.server.relative_move(self.axis, move)

    @inlineCallbacks
    def move_neg(self, x):
        move = -self.step_size.value()
        yield self.server.relative_move(self.axis, move)
    
    @inlineCallbacks
    def move_absolute(self, x):
        move = self.absolute_position_spin.value()
        yield self.server.absolute_move(self.axis, move)

    def updatePosition(self, pos):
        # set absolute position label and spin boxes to the new current position
        self.absolute_position_label.setText('current:   %d' % pos)
        self.absolute_position_spin.setValue(pos)

    def closeEvent(self, x):
        self.reactor.stop()

class PICOMOTOR_CONTROL(QtGui.QWidget):

    SIGNALID = 429162

    def __init__(self, reactor, cxn = None):
        QtGui.QWidget.__init__(self)
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.cxn = cxn
        self.connect()

    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection()
            yield self.cxn.connect()
        self.context = yield self.cxn.context()

        # initUI seems to need to be called from here
        # rather than __init__(), otherwise it doesn't
        # recognize self.context. Something about the order
        # of things getting called by the reactor
        self.initUI()
        yield self.initialize()

    @inlineCallbacks
    def initialize(self):
        server = yield self.cxn.get_server('PicomotorServer')

        # listen for signal__position_change and call self.followSignal when it occurs
        yield server.signal__position_change(self.SIGNALID, context = self.context)
        yield server.addListener(listener = self.followSignal, source = None, ID = self.SIGNALID, context = self.context)

        # update the positions
        for key in list(self.axes.keys()):
            yield server.get_position(key)
        
    def initUI(self):
        grid = QtGui.QGridLayout()
        reactor = self.reactor
        
        self.axes = {}
        for label, channel, (x, y) in widgets:
            axis = PICOMOTOR_AXIS(label, channel, reactor, self.cxn, self.context)
            grid.addWidget(axis, x, y)
            self.axes[channel] = axis

        self.setLayout(grid)

    def followSignal(self, x, y):
        # y is the message passed by the signal, i.e. (axis, new_position)
        channel, new_position = y
        self.axes[channel].updatePosition(new_position)

    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == '__main__':

    app = QtGui.QApplication([])
    from . import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    window = PICOMOTOR_CONTROL(reactor)
    window.show()
    reactor.run()
