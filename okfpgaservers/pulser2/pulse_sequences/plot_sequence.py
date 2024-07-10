from matplotlib import pyplot
import numpy as np

class SequencePlotter():
    """Can be used to plot the human readable form of a pulse sequence"""
    def __init__(self, sequence, dds, channels):
        self.seq = sequence
        self.dds = dds
        self.channels = channels
        self.plot = pyplot.figure()
        self.offset = 0 #control the y coordinate where the lines are drawn
    
    def makeNameDict(self):
        #swapping names of channels first
        chan = self.channels
        names = np.copy(chan[:,0])
        chan[:,0] = chan[:,1]
        chan[:,1] = names
        d = dict(chan)
        return d
    
    def extractInfo(self):
        times = np.array(self.seq.transpose()[0], dtype = np.float)
        l =  self.seq.transpose()[1]
        flatten = lambda x: [int(i) for i in x]
        switches = np.array( map(flatten, l) )
        switches = switches.transpose()
        return times,switches
    
    def getCoords(self, times, switches):
        '''takes the switching times and converts it to a list of coordiantes for plotting'''
        x = [times[0]]
        y = [switches[0]]   
        prev = switches[0]
        for i,switch in enumerate(switches[:-1]):
            if switch > prev:
                x.extend([times[i]]*2)
                y.extend([0,1])
            elif switch < prev:
                x.extend([times[i]]*2)
                y.extend([1,0])
            prev = switch
        x.append(times[-2])
        y.append(switches[-2])
        return np.array(x),np.array(y)
                 
    def makePlot(self):
        advance,reset = self.drawTTL()
        self.drawDDS(advance,reset)
        pyplot.xlabel('Time (sec)')
        pyplot.show()
        
    def drawTTL(self):
        advanceDDS = []
        resetDDS = []
        times,switches = self.extractInfo()
        nameDict = self.makeNameDict()
        for number,channel in enumerate(switches):
            if channel.any(): #ignore empty channels
                x,y = self.getCoords(times, channel)
                y = 3 * y + self.offset #offset the y coordinates
                label = nameDict[str(number)]
                if label == 'AdvanceDDS':
                    advanceDDS = x,y
                if label == 'ResetDDS':
                    resetDDS = x,y
                label = 'TTL ' + label
                pyplot.plot(x, y)
                pyplot.annotate(label, xy = (0,  self.offset + 1.5), horizontalalignment = 'right')
                self.offset += 4
        return advanceDDS,resetDDS
    
    def drawDDS(self, advance, reset):
        advance =  list(self.getRisingEdges(*advance))
        stop = self.getRisingEdges(*reset)
        advance.extend(stop)
        try:
            lastChannel = self.dds[0][0]
        except IndexError:
            return
        freqs = []
        ampls = []
        while True:
            try:
                channel, freq, ampl = self.dds.pop(0)
            except IndexError:
                self.addDDSPlot(lastChannel, freqs, ampls, advance)
                break
            if channel == lastChannel:
                freqs.append(freq)
                ampls.append(ampl)
            else:
                self.addDDSPlot(lastChannel, freqs, ampls, advance)
                lastChannel = channel
                freqs = [freq]
                ampls = [ampl]
        self.drawVerticals(advance)
    
    def getRisingEdges(self, x, y):
        '''looks at rising edges of y and returns the corresponding values of x'''
        rising = np.ediff1d(y, to_begin = 0) > 0
        return x[rising]
    
    def addDDSPlot(self, channel, freqs, ampls, advance):
        #each x coordiante appears twice except for the first one and last one
        x, y = self.getDDSCoordinates(advance, ampls)
        y = (np.array(y)  + 63.0) / 20.0 + self.offset #normalizes the amplitude -63 to -3 to height between 0 and 3
        label =  'DDS: ' + channel + ' Amplitude '
        pyplot.plot(x, y)
        pyplot.annotate(label, xy = (0,  self.offset + 1.5), horizontalalignment = 'right')
        self.offset += 4
        x, y = self.getDDSCoordinates(advance, freqs)
        y = np.array(y) / 250.0 + self.offset #normalizes the amplitude 0 to 250 to height between 0 and 3
        pyplot.plot(x, y, label = 'DDS Freq' + channel )
        label =  'DDS: ' + channel + ' Frequency '
        pyplot.annotate(label, xy = (0,  self.offset + 1.5), horizontalalignment = 'right')
        self.offset += 4
    
    def getDDSCoordinates(self, advance, ampls):
        x = [0]
        y = []
        for pt_x,pt_y in zip(advance,ampls):
            x.extend([pt_x,pt_x])
            y.extend([pt_y,pt_y])
        x = x[:-1]
        return x,y
    
    def drawVerticals(self, advances):
        for x in advances:
            pyplot.axvline(x, alpha = 0.3, color = '0.35', linestyle = '--')