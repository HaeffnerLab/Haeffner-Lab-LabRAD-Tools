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

class gridGraphConfig():
    def __init__(self, tab, config_list):
        self.tab = tab
        self.config_list = config_list[0::3]
        self.row_list = config_list[1::3]
        self.column_list = config_list[2::3]

        self.graphs = len(self.config_list)


tabs =[
    gridGraphConfig('current', [graphConfig('current', max_datasets = 1), 0, 0]),
    gridGraphConfig('pmt', [graphConfig('pmt', ylim=[0,30], isScrolling=True, max_datasets = 1, show_points = False), 0, 0]),
    gridGraphConfig('spectrum', [graphConfig('spectrum'), 0, 0]),
    gridGraphConfig('rabi', [graphConfig('rabi'), 0, 0]),
    gridGraphConfig('calibrations', [
                      graphConfig('car1'), 0, 0,
                      graphConfig('car2'), 0, 1,                      
                      graphConfig('radial1'), 1, 0,
                      graphConfig('radial2'), 1, 1]),
    gridGraphConfig('molmer-sorensen',[
                      graphConfig('ms_time'), 0, 0,
                      graphConfig('local_stark'), 0, 1]),

    gridGraphConfig('vaet',[
                      graphConfig('vaet_time'), 0, 0,
                      graphConfig('vaet_delta'), 0, 1]),
    gridGraphConfig('parity', [graphConfig('parity'), 0, 0]),
    gridGraphConfig('testgrid',
        [
            graphConfig('fig1'), 0, 0,
            graphConfig('fig2'), 0, 1,
            graphConfig('fig3'), 2, 2,
            graphConfig('fig4'), 1, 2
        ]),
    gridGraphConfig('testgrid2',
        [
            graphConfig('fig1123'), 0, 0,
        ])
]

