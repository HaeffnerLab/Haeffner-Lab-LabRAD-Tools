# track sidebands
from labrad.server import setting, LabradServer, Signal
from labrad.units import WithUnit
from twisted.internet.defer import returnValue, inlineCallbacks
import numpy as np
import time


class SidebandTracker(LabradServer):
    """ Tracks sideband drifts """

    name = 'Sideband Tracker'

    onNewFit = Signal( 768120, 'signal: new fit', '' )

    @inlineCallbacks
    def initServer(self):

        self.start_time = time.time()
        self.dv = None

        self.radial_1_fit = None
        self.radial_2_fit = None
        self.measurements = {'radial1': np.array([])
                             'radial2': np.array([])
                             }

        self.t_measure = {'radial1': np.array([]),
                          'radial2': np.array([])
                          }

        self.fit = {'radial1': None,
                    'radial2': None
                    }

    @inlineCallbacks
    def connect_data_vault(self):

        try:
            self.dv = yield self.client.data_vault

            save_1 = ['', 'Drift_Tracking', 'radial1']
            save_2 = ['', 'Drift_Tracking', 'radial2']

        except AttributeError:
            self.dv = None


    @setting(1, 'Set Measurement', mode = 's', frequency = 'v[MHz]', returns = '')
    def set_measurement(self, c, mode, frequency):
        '''Take a new radial mode measurement and perform tracking'''

        t_measure = time.time() - self.start_time
        assert (mode == 'radial1') or (mode == 'radial2')
        self.measurements[mode] = np.append(self.measurements[mode], frequency['MHz'])
        self.t_measure[mode] = np.append(self.t_measure[mode], t_measure)
        self.do_fit(mode)

    @setting(2, 'Remove Measurement', mode = 's', point = 'i', returns = '')
    def remove_measurement(self, c, mode, point):
        """Remove the point, can also be negative to count from the end"""

        try:
            self.measurements[mode] = np.delete(self.measurements[mode], point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit(mode)

    @setting(3, 'Get Current Frequency', mode = 's', returns = 'v[MHz]')
    def get_current_frequency(self, c, mode):
        """Return the projected frequency of the selected mode"""

        current_time = time.time() - self.start_time
        frequency = self.evaluate(current_time, mode)
        frequency = WithUnit(frequency, 'MHz')
        return frequency

    def do_fit(self, mode):

        x = self.t_measure[mode]
        y = self.measurements[mode]

        if len(y) >= 2:
            fit = np.polyfit(x, y, deg = 1)
            self.fit[mode] = fit
        else:
            self.fit[mode] = np.array([0, y[0]])

    def evaluate(self, t, mode):
        fit = self.fit[mode]
        prediction = np.polyval(fit, t)
        return prediction
