# test plotting window in pyqtgraph

import pyqtgraph as pg
import numpy as np
import random
from PyQt4 import QtGui

class Graph(QtGui.QWidget):

    def __init__(self, parent=None):
        super(Graph, self).__init__(parent)
        self.initUI()

    def initUI(self):
        x = np.linspace(0,100,100)
        y = [random.random() for k in x]
        y2 = [random.random() for k in x]
        self.pw = pg.PlotWidget()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.pw)
        self.setLayout(layout)
        #self.pw = pg.plot([],[])
        self.legend = self.pw.addLegend()
        self.pw.setXRange(1,503)
        self.pw.setYRange(-2, 2)
        p1=self.pw.plot(x,y, pen='r', name='plot1')
        p2=self.pw.plot(x, y2, pen='g', name='plot2')
        self.pw.removeItem(p2)
        self.legend.removeItem('plot2')
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    main = Graph()
    main.show()
    sys.exit(app.exec_())
