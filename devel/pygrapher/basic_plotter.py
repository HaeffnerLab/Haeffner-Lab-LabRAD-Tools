from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QTAgg as NavigationToolbar)
from PyQt4 import QtCore, QtGui
import matplotlib.animation as animation

from twisted.internet.threads import blockingCallFromThread
from twisted.internet.defer import Deferred

class Basic_Matplotlib_Plotter(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Basic_Matplotlib_Plotter, self).__init__(parent)
        self.artists = {}
        self.should_stop = False
        self.create_layout()
    
    def should_continue(self):
        d = Deferred()
        
#         blockingCallFromThread()
        while True:
            if self.should_stop: return
            yield True

    def create_layout(self):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.fig.set_facecolor('w')
        self.fig.set_tight_layout(True)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        self.axes.set_xlim([-10,1000])
        self.axes.set_ylim([-10,1000])
        self.ani = animation.FuncAnimation(self.fig, self.update_figure, self.should_continue, interval=50, blit=False)
        self.setLayout(vbox)
    
    def update_figure(self, _input = None):
        updated_arists = []
        for name, (artist, updated, data) in self.artists.iteritems():
            if updated:
                artist.set_data(data)
                self.artists[name][1] = False
                updated_arists.append(artist)
        return updated_arists
            
    def add_artst(self, name):
        line, = self.axes.plot([],[], '-o', markersize = 2.0, label = name)
        self.axes.legend()
        self.artists[name] = [line, False, ([],[])]
    
    def set_data(self, name, data):
        try:
            #updating the data
            self.artists[name][1] = True
            self.artists[name][2] = data
        except KeyError:
            raise Exception("No such artist found")
    
    def hide(self, name, shown):
        try:
            #updating the data
            self.artists[name][0].set_visible(shown)
        except KeyError:
            raise Exception("No such artist found")
        self.canvas.draw()
        
    def handle_close(self):
        self.should_stop = True
        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    form = Basic_Matplotlib_Plotter()
    form.show()
    app.exec_()