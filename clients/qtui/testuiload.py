#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore, QtWidgets, uic

class DC_CONTROL(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi('dconrf.ui',self)

app = QtWidgets.QApplication(sys.argv)
icon = DC_CONTROL()
icon.show()
app.exec_()

 
