from GraphWidget import Graph

'''
This is just the Graph with the update function
modified to also do scrolling
'''

class ScrollingGraph(Graph):

    def __init__(self, name, reactor, parent = None, ylim = [0,1]):
        super(ScrollingGraph, self).__init__(name, reactor, parent, ylim)

    def update_figure(self, _input = None):
        artists = []
        for ident, (artist, dataset, index) in self.artists.iteritems():
            x = dataset.data[:,0]
            y = dataset.data[:,index+1]
            artist.set_data((x,y))
            artists.append(artist)
        try:
            pointsToKeep = 100
            if len(x) < pointsToKeep:
                self.set_xlimits( [min(x), max(x)] )
            else:
                # see if we need to redraw
                xmin_cur, xmax_cur = self.current_limits
                x_cur = x[-1] # current largest x value
                window_width = xmax_cur - xmin_cur
                
                # scroll if we've reached 75% of the window
                if (x_cur - xmin_cur > 0.75*window_width):
                    shift = (xmax_cur - xmin_cur)/2.0
                    xmin = xmin_cur + shift
                    xmax = xmax_cur + shift
                    self.set_xlimits( [xmin, xmax] )
                    #plt.draw()
        except:
            pass
        return artists

