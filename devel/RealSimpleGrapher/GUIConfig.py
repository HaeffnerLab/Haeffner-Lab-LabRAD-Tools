'''
Configuration settings for Grapher gui
'''
import pyqtgraph as pg
pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'y')

class graphConfig():
    def __init__(self, name, ylim=[0,1], isScrolling=False, max_datasets = 6,
                 show_points = True):
        self.name = name
        self.ylim = ylim
        self.isScrolling = isScrolling
        self.max_datasets = max_datasets
        self.graphs = 1 # just a single graph
        self.show_points = show_points

class doubleGraphConfig():
    def __init__(self, tab, config1, config2):
        self.tab = tab
        self.config1 = config1
        self.config2 = config2
        self.graphs = 2

class quadGraphConfig():
    def __init__(self, tab, config1, config2, config3, config4):
        self.tab = tab
        self.config1 = config1
        self.config2 = config2
        self.config3 = config3
        self.config4 = config4
        self.graphs = 4


tabs =[
    graphConfig('current', max_datasets = 1),
    graphConfig('pmt', ylim=[0,30], isScrolling=True, max_datasets = 1, show_points = False),
    graphConfig('spectrum'),
    graphConfig('rabi'),
    quadGraphConfig('calibrations',
                      graphConfig('car1'), graphConfig('car2'),
                      graphConfig('radial1'), graphConfig('radial2')),
    doubleGraphConfig('molmer-sorensen',
                      graphConfig('ms_time'), graphConfig('local_stark')),
       
    doubleGraphConfig('vaet',
                      graphConfig('vaet_time'), graphConfig('vaet_delta')),
    graphConfig('parity'),
    graphConfig('vaet_ms_det'),
]
