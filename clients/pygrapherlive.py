import sys
from PyQt4 import QtGui
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import time
import numpy as np
import labrad

##TODO1:faster load by reading in file directly
##TODO2;figure our when live plot gets slow, then implement limiting the number of points
##TODO3:switch between live graph mode and whole graph mode: where the csv file is loaded with no live update
##TODO4:toggle button for autoscrolling, plus qdoublebox how many points to display
##TODO5:be able to pick name of the dataset QListBox/QListView, check which lines are plotted
##TODO6;clean up code, add intro, upload to sourceforge

GraphRefreshTime = 100; #ms, how often plot updates
#SEE TODO2,TODO3
MaxDataPointsLive = 5000;
scrollfrac = .75; #data reaches this much of the screen before auto-scroll takes place
#SEE TODO5
DIRECTORY = 'PMT Counts'
DATASET = raw_input("enter dataset for plotting, i,e 114: ")
DATASET = int(DATASET)

class Qt4MplCanvas(FigureCanvas):
	"""Class to represent the FigureCanvas widget"""
	def __init__(self, parent):	
		#isntantiate figure
		self.fig = Figure()
		FigureCanvas.__init__(self, self.fig)
		#create plot 
		self.ax = self.fig.add_subplot(111)
		self.ax.grid()
		self.ax.set_xlim(0, 100)###add constants
		self.ax.set_ylim(-1, 100)
		self.ax.set_autoscale_on(False) # disable figure-wide autoscale
		self.plots,self.data = self.generateInitPlot()
		self.ax.legend()
		self.draw()
		self.old_size = self.ax.bbox.width, self.ax.bbox.height
		self.ax_background = self.copy_from_bbox(self.ax.bbox)
		self.cnt = 0
		self.timer = self.startTimer(GraphRefreshTime)
		
	#loads in existing data from datavault, returns a list of plots
	def generateInitPlot(self):
                self.cxn = labrad.connect()
                self.dvault = self.cxn.data_vault
                self.dvault.cd(DIRECTORY)
                self.dvault.open(DATASET)
                plotnum = len(self.dvault.variables()[1]) #number of things to plot
                plots = [[]]*plotnum
                print 'loading data'
                data = self.dvault.get().asarray
                print data[3:100,3]
                dep = data.transpose()[0]
                indep1 = data.transpose()[1]
                indep2 = data.transpose()[2]
                indep3 = data.transpose()[3]
                plots[0] = self.ax.plot(dep.tolist(),indep1.tolist(),label = '866 ON',animated=True)
                plots[1] = self.ax.plot(dep.tolist(),indep2.tolist(),label = '866 OFF', animated=True)
                plots[2] = self.ax.plot(dep.tolist(),indep3.tolist(),label = 'Differential ', animated=True)
                plots = self.flatten(plots)
                return plots,data
        
	def timerEvent(self, evt):
                if(self.cnt == 0): #draw initial data
                         # redraw just the lines
                        self.ax.draw_artist(self.plots[0])
                        self.ax.draw_artist(self.plots[1])
                        self.ax.draw_artist(self.plots[2])
                        #  redraw the cached axes rectangle
                        self.blit(self.ax.bbox)
                        self.cnt = self.cnt+1
		tstartupdate = time.clock()
		newdatal = self.dvault.get()
		if(len(newdatal[0])==0):
                        print 'no new data available'
                else:
                        #append new data to the datasets                     
                        newdata = np.array(newdatal)
                        self.data = np.append(self.data,newdata,0)
                        current_size = self.ax.bbox.width, self.ax.bbox.height
                        if self.old_size != current_size: #have to redraw whole canvas if size changes
                                print 'size change'
                                self.old_size = current_size
                                self.ax.clear()
                                self.ax.grid()
                                self.ax.legend()
                                self.draw()
                                self.ax_background = self.copy_from_bbox(self.ax.bbox)
                                self.restore_region(self.ax_background, bbox=self.ax.bbox)
                        # update the plot data
                        dep = self.data.transpose()[0]
                        indep1 = self.data.transpose()[1]
                        indep2 = self.data.transpose()[2]
                        indep3 = self.data.transpose()[3]
                        self.plots[0].set_data(dep,indep1)
                        self.plots[1].set_data(dep,indep2)
                        self.plots[2].set_data(dep,indep3)
                        # redraw just the lines
                        self.ax.draw_artist(self.plots[0])
                        self.ax.draw_artist(self.plots[1])
                        self.ax.draw_artist(self.plots[2])
                        #  redraw the cached axes rectangle
                        self.blit(self.ax.bbox)
		tstopupdate = time.clock()
		print tstopupdate - tstartupdate
		if(1000*(tstopupdate - tstartupdate) > GraphRefreshTime):
			print 'WARNING: can not keep up update rate of ' + str(GraphRefreshTime) + 'ms'
		self.updateBoundary()
		self.cnt += 1
	#provides dynamic scrolling of data on the screen
	def updateBoundary(self):
                cur = self.data.transpose()[0][-1]
		xmin, xmax = self.ax.get_xlim()
		xwidth = xmax - xmin
		# if current x position exceeds certain x coordinate, update the screen
		if (cur > scrollfrac * xwidth + xmin):
			xmin = cur - xwidth/4
			xmax = xmin + xwidth
			self.ax.set_xlim(xmin, xmax)
			self.draw()
        #to flatten lists (for some reason not built in)
        def flatten(self,l):
                out = []
                for item in l:
                        if isinstance(item, (list, tuple)):
                                out.extend(self.flatten(item))
                        else:
                                out.append(item)
                return out

class ApplicationWindow(QtGui.QMainWindow):
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
		self.setWindowTitle("Live Grapher")
		self.main_widget = QtGui.QWidget(self)
		# create a vertical box layout widget
		vbl = QtGui.QVBoxLayout(self.main_widget)
		# instantiate our Matplotlib canvas widget
		qmc = Qt4MplCanvas(self.main_widget)
		# instantiate the navigation toolbar
		ntb = NavigationToolbar(qmc, self.main_widget)
		vbl.addWidget(ntb)
		vbl.addWidget(qmc)
		# set the focus on the main widget
		self.main_widget.setFocus()
		self.setCentralWidget(self.main_widget)

qApp = QtGui.QApplication(sys.argv)
aw = ApplicationWindow()
aw.show()
sys.exit(qApp.exec_())
