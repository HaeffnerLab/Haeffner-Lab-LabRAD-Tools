#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore,uic

class DC_CONTROL(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        uic.loadUi('dconrf.ui',self)

app = QtGui.QApplication(sys.argv)
icon = DC_CONTROL()
icon.show()
app.exec_()

 
