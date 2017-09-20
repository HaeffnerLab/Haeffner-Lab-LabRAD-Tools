from PyQt4 import QtGui,QtCore
from twisted.internet.defer import inlineCallbacks
import time
import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *


class thread(QtCore.QThread):

    def __init__(self, x, y, *args, **keywords):
        QtCore.QThread.__init__(self, *args, **keywords)
        self.killed = False
        self.x = x
        self.y = y


    def start(self, QThread_Priority_priority=None):
        self.__run_backup = self.run
        #print '__run_backup finish'
        self.run = self.__run
        #print '__run'
        QtCore.QThread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            #print 'global why==call true'
            return self.localtrace
        else:
            #print 'global why==call false'
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                print 'lobal why==line true'
                raise SystemExit()
        return self.localtrace

    def kill(self):
        self.killed = True
        print 'kill true'

    def run(self):
        if(self.y == 1):
            self.x.getback1()
        else:
            self.x.getback2()


class InjectionLock_Control(QtGui.QFrame):
    def __init__(self, reactor, parent=None):

        self.reactor = reactor

        self.connect()

        super(InjectionLock_Control, self).__init__(parent)

        grid = QtGui.QGridLayout()
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)

        self.q1Edit = QtGui.QDoubleSpinBox()
        self.q1Edit.setSingleStep(0.01)
        self.q1Edit.setValue(2.0)
        self.q1Edit.setSuffix(' V')
        self.q1Edit.setMinimum(0.1)
        self.q1Edit.setMaximum(10.0)

        self.q2Edit = QtGui.QDoubleSpinBox()
        self.q2Edit.setSingleStep(0.01)
        self.q2Edit.setValue(6.0)
        self.q2Edit.setSuffix(' V')
        self.q2Edit.setMinimum(0.1)
        self.q2Edit.setMaximum(10.0)

        self.q3Edit = QtGui.QDoubleSpinBox()
        self.q3Edit.setSingleStep(0.01)
        self.q3Edit.setValue(1.0)
        self.q3Edit.setSuffix(' V')
        self.q3Edit.setMinimum(0.1)
        self.q3Edit.setMaximum(10.0)

        self.q4Edit = QtGui.QDoubleSpinBox()
        self.q4Edit.setSingleStep(0.01)
        self.q4Edit.setValue(4.0)
        self.q4Edit.setSuffix(' V')
        self.q4Edit.setMinimum(0.1)
        self.q4Edit.setMaximum(10.0)

        grid.addWidget(QtGui.QLabel('729super  Scan Range:'), 1, 0)
        grid.addWidget(self.q1Edit, 1, 1)

        grid.addWidget(QtGui.QLabel('729inject  Scan Range:'), 2, 0)
        grid.addWidget(self.q2Edit, 1, 2)

        grid.addWidget(self.q3Edit, 2, 1)

        grid.addWidget(self.q4Edit, 2, 2)

        self.applyBtn = QtGui.QPushButton('Relock', self)
        self.applyBtn.clicked.connect(self.start_thread_supervisor)
        grid.addWidget(self.applyBtn, 1, 3)

        self.stopBtn = QtGui.QPushButton('Stop', self)
        self.stopBtn.clicked.connect(self.stop_thread_supervisor)
        grid.addWidget(self.stopBtn, 1, 4)

        self.applyBtn2 = QtGui.QPushButton('Relock', self)
        self.applyBtn2.clicked.connect(self.start_thread_slave)

        grid.addWidget(self.applyBtn2, 2, 3)

        self.stopBtn2 = QtGui.QPushButton('Stop', self)
        self.stopBtn2.clicked.connect(self.stop_thread_slave)

        grid.addWidget(self.stopBtn2, 2, 4)

        self.setLayout(grid)
        self.setGeometry(500, 500, 1000, 300)
        self.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=10))
        self.thread_supervisor = thread(self,1)
        self.thread_slave = thread(self,2)

        self.stopBtn.setEnabled(False)
        self.stopBtn2.setEnabled(False)



    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        try:
            self.cxn = yield connectAsync('192.168.169.49', password='lab', tls_mode='off')
        except:
            self.cxn = yield connectAsync('192.168.169.49', password='lab')
        yield self.setupListeners()

    @inlineCallbacks
    def setupListeners(self):

        self.inj = yield self.cxn['injectionlock']
        self.initialized = True
        self.setEnabled(True)

    def start_thread_supervisor(self):

        #self.connect(self.th, SIGNAL('loop()'), lambda x=2: self.loopfunction(x), Qt.AutoConnection)
        if(self.inj.get_supervisor_status() == False):

            self.thread_supervisor.start()
            self.stopBtn.setEnabled(True)
            print 'supervisor start'
        else:
            app = QApplication(sys.argv)
            msg_box = QMessageBox(QMessageBox.Warning, "Alert", "Others are relocking supervisor now!")
            msg_box.show()
            app.exec_()

    def stop_thread_supervisor(self):
        #self.inj.stop_supervisor()
        print 'supervisor stop'
        self.applyBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    def start_thread_slave(self):

        #self.connect(self.th, SIGNAL('loop()'), lambda x=2: self.loopfunction(x), Qt.AutoConnection)
        if(self.inj.get_slave_status() == False):

            self.thread_slave.start()
            self.stopBtn2.setEnabled(True)
            print 'slave start'
        else:
            app = QApplication(sys.argv)
            msg_box = QMessageBox(QMessageBox.Warning, "Alert", "Others are relocking slave now!")
            msg_box.show()
            app.exec_()

    def stop_thread_slave(self):
        #self.inj.stop_slave()
        print 'slave stop'
        self.applyBtn2.setEnabled(True)
        self.stopBtn2.setEnabled(False)


    def getback1(self):
        self.applyBtn.setEnabled(False)
        count1 = 0
        for text in self.q1Edit.text():
            if (text == ' '):
                break;
            count1 += 1
        count2 = 0
        for text in self.q2Edit.text():
            if (text == ' '):
                break;
            count2 += 1
        self.inj.relock_supervisor(float(self.q1Edit.text()[0:count1]), float(self.q2Edit.text()[0:count2]))
        self.applyBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        app = QApplication(sys.argv)
        msg_box = QMessageBox(QMessageBox.NoIcon, "Finish", "Supervisor is locked!")
        msg_box.show()
        app.exec_()

    def getback2(self):
        self.applyBtn2.setEnabled(False)
        count3 = 0
        for text in self.q3Edit.text():
            if (text == ' '):
                break;
            count3 += 1
        count4 = 0
        for text in self.q4Edit.text():
            if (text == ' '):
                break;
            count4 += 1

        self.inj.relock_slave(float(self.q3Edit.text()[0:count3]), float(self.q4Edit.text()[0:count4]))
        self.applyBtn2.setEnabled(True)
        self.stopBtn2.setEnabled(False)
        app = QApplication(sys.argv)
        msg_box = QMessageBox(QMessageBox.NoIcon, "Finish", "Slave is locked!")
        msg_box.show()
        app.exec_()

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == '__main__':
    a = QtGui.QApplication([])
    import qt4reactor

    qt4reactor.install()
    from twisted.internet import reactor

    injectionlock_control = InjectionLock_Control(reactor)
    injectionlock_control.show()
    reactor.run()