import sys
from PyQt4 import QtGui
import labrad
import time
import thread
import threading

class Widget(QtGui.QDialog):

    def __init__(self, parent=None):

        self.cxn_laserroom = labrad.connect('192.168.169.49', password='lab', tls_mode='off')
        self.inj = self.cxn_laserroom.injectionlock

        super(Widget, self).__init__(parent)

        self.q1Edit = QtGui.QDoubleSpinBox()
        self.q1Edit.setSingleStep(0.01)
        self.q1Edit.setValue(0.1)

        self.q2Edit = QtGui.QDoubleSpinBox()
        self.q2Edit.setSingleStep(0.01)
        self.q2Edit.setValue(2.9)

        self.q3Edit = QtGui.QDoubleSpinBox()
        self.q3Edit.setSingleStep(0.01)
        self.q3Edit.setValue(0.1)

        self.q4Edit = QtGui.QDoubleSpinBox()
        self.q4Edit.setSingleStep(0.01)
        self.q4Edit.setValue(5.1)

        grid = QtGui.QGridLayout()
        grid.setSpacing(20)

        grid.addWidget(QtGui.QLabel('Supervisor Scan Range:'), 1, 0)
        grid.addWidget(self.q1Edit, 1, 1)

        grid.addWidget(QtGui.QLabel('        Slave Scan Range:'), 2, 0)
        grid.addWidget(self.q2Edit, 1, 2)

        grid.addWidget(self.q3Edit, 2, 1)

        grid.addWidget(self.q4Edit, 2, 2)

        self.applyBtn = QtGui.QPushButton('Relock', self)
        self.applyBtn.clicked.connect(self.startthread1)

        grid.addWidget(self.applyBtn,1,3)


        self.applyBtn2 = QtGui.QPushButton('Relock', self)
        self.applyBtn2.clicked.connect(self.startthread2)

        grid.addWidget(self.applyBtn2,2,3)

        self.setLayout(grid)
        self.setGeometry(300, 300, 550, 150)



    @staticmethod
    def getData(parent=None):
        dialog = Widget(parent)
        dialog.setWindowTitle('Injection Lock')
        dialog.exec_()

    def startthread1(self):
        thread.start_new_thread(self.getback1, ("Thread-supervisor", 1, ))

    def startthread2(self):
        thread.start_new_thread(self.getback2, ("Thread-slave", 2, ))

    def getback1(self,name,num):
        self.applyBtn.setEnabled(False)
        print float(self.q1Edit.text())*float(self.q2Edit.text())
        time.sleep(3)
        self.applyBtn.setEnabled(True)
        #self.inj.relock_supervisor(float(self.q1Edit.text()),float(self.q2Edit.text()))

    def getback2(self,name,num):
        self.applyBtn2.setEnabled(False)
        print float(self.q3Edit.text())*float(self.q4Edit.text())
        time.sleep(3)
        self.applyBtn2.setEnabled(True)
        #self.inj.relock_slave(float(self.q3Edit.text()),float(self.q4Edit.text()))

def main():
    app = QtGui.QApplication([])
    window = Widget()
    data = window.getData()


if __name__ == '__main__':
    main()