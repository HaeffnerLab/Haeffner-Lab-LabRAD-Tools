from PyQt5 import QtCore, QtGui, QtWidgets
from twisted.internet.defer import inlineCallbacks
import time
import sys



class InjectionLock_Control(QtWidgets.QFrame):
    def __init__(self, reactor, parent=None):

        self.reactor = reactor

        self.connect()

        super(InjectionLock_Control, self).__init__(parent)

        grid = QtWidgets.QGridLayout()
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

        self.q1Edit = QtWidgets.QDoubleSpinBox()
        self.q1Edit.setSingleStep(0.01)
        self.q1Edit.setValue(2.0)
        self.q1Edit.setSuffix(' V')
        self.q1Edit.setMinimum(0.1)
        self.q1Edit.setMaximum(10.0)

        self.q2Edit = QtWidgets.QDoubleSpinBox()
        self.q2Edit.setSingleStep(0.01)
        self.q2Edit.setValue(6.0)
        self.q2Edit.setSuffix(' V')
        self.q2Edit.setMinimum(0.1)
        self.q2Edit.setMaximum(10.0)

        self.q3Edit = QtWidgets.QDoubleSpinBox()
        self.q3Edit.setSingleStep(0.01)
        self.q3Edit.setValue(1.0)
        self.q3Edit.setSuffix(' V')
        self.q3Edit.setMinimum(0.1)
        self.q3Edit.setMaximum(10.0)

        self.q4Edit = QtWidgets.QDoubleSpinBox()
        self.q4Edit.setSingleStep(0.01)
        self.q4Edit.setValue(4.0)
        self.q4Edit.setSuffix(' V')
        self.q4Edit.setMinimum(0.1)
        self.q4Edit.setMaximum(10.0)

        grid.addWidget(QtWidgets.QLabel('729super  Scan Range:'), 1, 0)
        grid.addWidget(self.q1Edit, 1, 1)

        grid.addWidget(QtWidgets.QLabel('729inject  Scan Range:'), 2, 0)
        grid.addWidget(self.q2Edit, 1, 2)

        grid.addWidget(self.q3Edit, 2, 1)

        grid.addWidget(self.q4Edit, 2, 2)

        self.applyBtn = QtWidgets.QPushButton('Relock', self)
        self.applyBtn.clicked.connect(self.start_thread_supervisor)
        #self.applyBtn.clicked.connect(self.getback1)
        grid.addWidget(self.applyBtn, 1, 3)

        self.stopBtn = QtWidgets.QPushButton('Stop', self)
        self.stopBtn.clicked.connect(self.stop_thread_supervisor)
        grid.addWidget(self.stopBtn, 1, 4)
        
        self.statusBtn = QtWidgets.QPushButton('Status', self)
        self.statusBtn.clicked.connect(self.get_status_supervisor)
        grid.addWidget(self.statusBtn, 1, 5)

        self.applyBtn2 = QtWidgets.QPushButton('Relock', self)
        self.applyBtn2.clicked.connect(self.start_thread_slave)
        #self.applyBtn2.clicked.connect(self.getback2)

        grid.addWidget(self.applyBtn2, 2, 3)

        self.stopBtn2 = QtWidgets.QPushButton('Stop', self)
        self.stopBtn2.clicked.connect(self.stop_thread_slave)

        grid.addWidget(self.stopBtn2, 2, 4)
        
        self.statusBtn2 = QtWidgets.QPushButton('Status', self)
        self.statusBtn2.clicked.connect(self.get_status_slave)
        grid.addWidget(self.statusBtn2, 2, 5)

        self.setLayout(grid)
        self.setGeometry(500, 500, 1000, 300)
        self.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=10))

        #self.stopBtn.setEnabled(False)
        #self.stopBtn2.setEnabled(False)



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

    @inlineCallbacks
    def get_status_supervisor(self, c):
        relock_supervisor_alive = yield self.inj.get_supervisor_status()
        if(relock_supervisor_alive == True):
            msg_box1 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Still scanning!")
            msg_box1.exec_()
        elif(relock_supervisor_alive == False):
            msg_box2 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "Finish", "Not scanning!")
            msg_box2.exec_()
            
    
    @inlineCallbacks
    def get_status_slave(self, c):
        relock_slave_alive = yield self.inj.get_slave_status()
        if(relock_slave_alive == True):
            msg_box3 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Still scanning!")
            msg_box3.exec_()
        elif(relock_slave_alive == False):
            msg_box4 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "Finish", "Not scanning!")
            msg_box4.exec_()

    @inlineCallbacks
    def start_thread_supervisor(self, c):

        #self.connect(self.th, SIGNAL('loop()'), lambda x=2: self.loopfunction(x), Qt.AutoConnection)
        relock_supervisor_alive = yield self.inj.get_supervisor_status()
        relock_slave_alive = yield self.inj.get_slave_status()
        if(relock_supervisor_alive == False and relock_slave_alive== False):
            self.getback1()
            #self.stopBtn.setEnabled(True)
            print('supervisor start')
        elif(relock_supervisor_alive == False and relock_slave_alive== True):            
            msg_box5 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Slave is relocking now!")
            msg_box5.exec_()
        elif(relock_supervisor_alive == True and relock_slave_alive== False):
            msg_box6 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Supervisor is relocking")
            msg_box6.exec_()

    @inlineCallbacks
    def stop_thread_supervisor(self, c):
        relock_supervisor_alive = yield self.inj.get_supervisor_status()
        relock_slave_alive = yield self.inj.get_slave_status()
        if(relock_supervisor_alive == True and relock_slave_alive== False):
            self.inj.stop_supervisor()
            print('supervisor stop')
            
        elif(relock_supervisor_alive == False and relock_slave_alive == True):
            msg_box7 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Supervisor is not relocking")
            msg_box7.exec_()
        
        elif(relock_supervisor_alive == False and relock_slave_alive == False):
            msg_box8 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Nothing is relocking now!")
            msg_box8.exec_()
        #self.applyBtn.setEnabled(True)
        #self.stopBtn.setEnabled(False)
        
    @inlineCallbacks   
    def start_thread_slave(self, c):
        
        #self.connect(self.th, SIGNAL('loop()'), lambda x=2: self.loopfunction(x), Qt.AutoConnection)
        relock_supervisor_alive = yield self.inj.get_supervisor_status()
        relock_slave_alive = yield self.inj.get_slave_status()
        if(relock_supervisor_alive == False and relock_slave_alive== False):
            self.getback2()
            #self.stopBtn.setEnabled(True)
            print('slave start')
        elif(relock_supervisor_alive == False and relock_slave_alive== True):            
            msg_box9 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Slave is relocking now!")
            msg_box9.exec_()
        elif(relock_supervisor_alive == True and relock_slave_alive== False):
            msg_box10 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Supervisor is relocking now!")
            msg_box10.exec_()
             

    @inlineCallbacks 
    def stop_thread_slave(self, c):
        relock_supervisor_alive = yield self.inj.get_supervisor_status()
        relock_slave_alive = yield self.inj.get_slave_status()
        if(relock_supervisor_alive == False and relock_slave_alive== True):
            self.inj.stop_slave()
            print('supervisor stop')
            
        elif(relock_supervisor_alive == True and relock_slave_alive == False):
            msg_box11 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Slave is not relocking")
            msg_box11.exec_()
        
        elif(relock_supervisor_alive == False and relock_slave_alive == False):
            msg_box12 = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Alert", "Nothing is relocking now!")
            msg_box12.exec_()



    def getback1(self):

        #self.stopBtn.setEnabled(True)
        #self.applyBtn.setEnabled(False)
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
        


    def getback2(self):
        #self.stopBtn2.setEnabled(True)
        #self.applyBtn2.setEnabled(False)
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
        
        

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == '__main__':
    a = QtWidgets.QApplication([])
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    injectionlock_control = InjectionLock_Control(reactor)
    injectionlock_control.show()
    reactor.run()
