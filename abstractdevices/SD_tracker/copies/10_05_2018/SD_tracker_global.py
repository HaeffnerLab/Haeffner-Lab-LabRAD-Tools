"""
### BEGIN NODE INFO
[info]
name = SD Tracker Global
version = 2.0
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from labrad.server import setting, LabradServer, Signal
from labrad.units import WithUnit
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.task import LoopingCall
import time
from SD_tracker_global_config import config as conf
from SD_calculator import Transitions_SD, fitter
from common.client_config import client_info as cl
import numpy
#from labrad.units import WithUnit

client_list = cl.client_list
keep_line_center_measurements_local = dict.fromkeys(client_list, conf.default_keep_line_center_measurements_local)
keep_line_center_measurements_global = dict.fromkeys(client_list, conf.default_keep_line_center_measurements_global)
keep_B_measurements_local = dict.fromkeys(client_list, conf.default_keep_B_measurements_local)
auto_update_rate = conf.auto_update_rate
clear_all_duration = conf.clear_all_duration

class SDTrackerGlobal(LabradServer):
    """Provides ability to track drifts of the SD line"""
    name = 'SD Tracker Global'
    
    onNewFit = Signal( 768120, 'signal: new fit', '' )
    for ite1, ite2 in enumerate(client_list):
        ite1 = 768121 + ite1
        ite3 = 'signal: new save {}'.format(ite2)
        exe_str = "onNewSave" + ite2.replace(' ', '') + " = Signal( 768121 + ite1, 'signal: new save " + ite2 + "', 's')"
        exec(exe_str)
    del ite1, ite2, ite3, exe_str
    
    #@inlineCallbacks
    def initServer(self):
        #Record server start time
        self.start_time = time.time()
        #Load default tracking durations and calculators
        self.keep_line_center_measurements_local = keep_line_center_measurements_local
        self.keep_line_center_measurements_global = keep_line_center_measurements_global
        self.keep_B_measurements_local = keep_B_measurements_local
        self.tr = Transitions_SD()
        self.fitter = fitter()
        #Create 8 dictionaries to store fit and nofit data for all clients
        self.t_measure_line_center = dict.fromkeys(client_list, numpy.array([]))
        self.t_measure_B = dict.fromkeys(client_list, numpy.array([]))
        self.t_measure_line_center_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.t_measure_B_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.line_center = dict.fromkeys(client_list, numpy.array([]))
        self.line_center_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.B_field = dict.fromkeys(client_list, numpy.array([]))
        self.B_field_nofit = dict.fromkeys(client_list, numpy.array([]))
        #Create 3 dictionaries to store fit parameters for local B fit, local line center fit and global line center fit for all clients
        self.line_center_fit_local = dict.fromkeys(client_list)
        self.B_fit_local = dict.fromkeys(client_list)
        self.line_center_fit_global = dict.fromkeys(client_list)
        #create 2 dictionaries to store global line center fit data points for all clients
        self.t_measure_line_center_fit_global_data = dict.fromkeys(client_list, numpy.array([]))
        self.line_center_fit_global_data = dict.fromkeys(client_list, numpy.array([]))
        #Create a dictionary to store global fit client lists for all clients
        self.global_fit_list = dict.fromkeys(client_list, [])
        #Create a dictionary to decide whether to return local one or global one when somebody calls a same setting
        self.bool_global = dict.fromkeys(client_list, False)
        #Data vault
        '''
        self.dv = {}
        yield self.connect_data_vault()
        yield self.setupListeners()
        '''
        #Auto update everything
        updater = LoopingCall(self.do_fit_global)
        updater.start(auto_update_rate)
    
    '''
    @inlineCallbacks
    def connect_data_vault(self):
        try:
            #reconnect to data vault and navigate to the directory
            self.dv = yield self.client.data_vault
            directory = list(conf.save_folder)
            localtime = time.localtime()
            dirappend = [time.strftime("%Y%b%d",localtime)]
            directory.extend(dirappend)
            yield self.dv.cd(directory, True)
            datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
            save_name = '{0} {1}'.format(conf.dataset_name, datasetNameAppend)
            self.line_center_dataset = yield self.dv.new(save_name, [('t', 'sec')], [('Cavity Drift','Line Center','MHz'),('Cavity Drift','B Field','gauss')])
            yield self.dv.add_parameter('start_time', time.time())
        except AttributeError:
            self.dv = None
        
    @inlineCallbacks
    def setupListeners(self):
        yield self.client.manager.subscribe_to_named_message('Server Connect', conf.signal_id, True)
        yield self.client.manager.subscribe_to_named_message('Server Disconnect', conf.signal_id+1, True)
        yield self.client.manager.addListener(listener = self.followServerConnect, source = None, ID = conf.signal_id)
        yield self.client.manager.addListener(listener = self.followServerDisconnect, source = None, ID = conf.signal_id+1)
    
    @inlineCallbacks
    def followServerConnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Data Vault':
            yield self.connect_data_vault()
        else:
            yield None
    
    @inlineCallbacks
    def followServerDisconnect(self, cntx, serverName):
        serverName = serverName[1]
        if serverName == 'Data Vault':
            self.dv = None
        yield None

    @inlineCallbacks
    def save_result_datavault(self, t_measure, freq, b_field, client):
        self.client_examination(client)
        try:
            yield self.dv.add((t_measure, freq, b_field))
        except AttributeError:
            print 'Data Vault Not Available, not saving'
            yield None
    '''

    def arraydict_join(self, dic, key_list = None):
        '''Create a joined array from selected keys in a dictionary'''
        array = numpy.array([])
        if key_list == None:
            for key in dic.keys():
                if type(dic[key]) == numpy.ndarray:
                    array = numpy.append(array, dic[key])
                else:
                    raise Exception('Value type in dictionary is not numpy.ndarray.')
        else:
            for key in key_list:
                if key not in dic.keys():
                    raise Exception('{0} not in {1}'.format(key, dic.keys()))
                elif type(dic[key]) == numpy.ndarray:
                    array = numpy.append(array, dic[key])
                else:
                    raise Exception('Value type in dictionary is not numpy.ndarray.')
        return array

    def client_examination(self, client):
        '''Examine whether client is in client list which consists of all clients'''
        if client not in client_list:
            raise Exception("{0} is not in client list: {1}".format(client, client_list))
        else:
            pass
    
    @setting(1, 'Get Transition Names', returns = '*s')
    def get_transitions(self, c):
        '''Returns the names of possible transitions'''
        return self.tr.transitions()
        
    @setting(2, 'Set Measurements', lines = '*(sv[MHz])', client = 's')
    def set_measurements(self, c, lines, client):
        '''
        Takes the names and frequencies of two lines and performs tracking.
        Input i.e.: ([("S-1/2D-1/2", U(-22.0, 'MHz')), ("S-1/2D-5/2", U(-27, 'MHz'))], 'lattice')
        '''
        self.client_examination(client)
        t_measure = time.time() - self.start_time
        if not len(lines) == 2: raise Exception ("Please provide measurement for two lines")
        name1,f1 = lines[0]
        name2,f2 = lines[1]
        if name1 not in self.tr.transitions() or name2 not in self.tr.transitions():
            raise Exception("Lines do not match known transitions")
        if name1 == name2: raise Exception("Provided Measurements must be of different lines")
        
        B,freq = self.tr.energies_to_magnetic_field( ( (name1,f1),(name2,f2) ))
        
        # arrays which contain the time when the measurement was taken
        self.t_measure_B[client] = numpy.append(self.t_measure_B[client], t_measure)
        self.t_measure_line_center[client] = numpy.append(self.t_measure_line_center[client], t_measure)

        # arrays of B_field and line center
        self.B_field[client] = numpy.append(self.B_field[client], B['gauss'])
        self.line_center[client] = numpy.append(self.line_center[client], freq['MHz'])
        
        # try to save to data vault
        # yield self.save_result_datavault(t_measure, freq['MHz'], B['gauss'])
        # save the epoch time, NOT the time since the software started t_measure
        #yield self.save_result_datavault(time.time(), freq['MHz'], B['gauss'], client)
        self.do_fit_local(client)
        exe_str = "self.onNewSave" + client.replace(' ', '') + "('linecenter_bfield')"
        exec exe_str

    @setting(13, "Set Measurements With One Line", line = '*(sv[MHz])', client = 's')
    def set_measurements_with_one_line(self, c, line, client):
        '''
        Takes the names and frequencies of one line, and get line center from fit parameters, and performs tracking.
        Input i.e.: ([("S-1/2D-1/2", U(-22.0, 'MHz')), 'lattice')
        '''
        self.client_examination(client)
        t_measure = time.time() - self.start_time
        name, f = line[0]
        freq = yield self.get_current_center(c, client)
        B = self.tr.energy_line_center_to_magnetic_field((name, f), freq)

        self.t_measure_B[client] = numpy.append(self.t_measure_B[client], t_measure)
        self.B_field[client] = numpy.append(self.B_field[client], B['gauss'])

        self.do_fit_local(client)
        exe_str = "self.onNewSave" + client.replace(' ', '') + "('bfield')"
        exec exe_str

    @setting(3, 'Set Measurements with Bfield and Line Center', B = '*(sv[gauss])', freq = '*(sv[MHz])', client = 's')
    def set_measurements_with_bfield_and_line_center(self, c, B, freq, client):
        '''
        takes the Bfield and the line center and sets up tracking
        Input i.e.: ([('bfield', U(5.0, 'gauss'))], [('line_center', U(-22.0, 'MHz'))], 'lattice')
        '''
        self.client_examination(client)

        t_measure = time.time() - self.start_time
       
        B = B[0][1]
        freq = freq[0][1]

        # arrays which contain the time when the measurement was taken
        self.t_measure_B[client] = numpy.append(self.t_measure_B[client] , t_measure)
        self.t_measure_line_center[client] = numpy.append(self.t_measure_line_center[client], t_measure)

        # arrays of B_field and line center
        self.B_field[client] = numpy.append(self.B_field[client] , B['gauss'])
        self.line_center[client] = numpy.append(self.line_center[client] , freq['MHz'])
        
        # try to save to data vault
        # yield self.save_result_datavault(t_measure, freq['MHz'], B['gauss'])
        # save the epoch time, NOT the time since the software started t_measure
        #yield self.save_result_datavault(time.time(), freq['MHz'], B['gauss'], client)
        self.do_fit_local(client)
        exe_str = "self.onNewSave" + client.replace(' ', '') + "('linecenter_bfield')"
        exec exe_str
    
    # @setting(12, 'Set Measurement One Line', line = 'sv[MHz]', client = 's', returns = '')
    # def set_measurement_one_line(self, c, line, client):
    #    ''' takes name and frequency of one line, and assumes the cavity position from previous data '''
    #    t_measure = time.time() - self.start_time
    #    name,f = line
    #    if name not in self.tr.transitions():
    #        raise Exception("Line does not match a known transition")

    @setting(14, "Set Measurements With Bfield", B = '*(sv[gauss])', client = 's')
    def set_measurements_with_bfield(self, c, B, client):
        '''
        takes the Bfield and sets up tracking
        Input i.e.: ([('bfield', U(5.0, 'gauss'))], 'lattice')
        '''
        self.client_examination(client)
        t_measure = time.time() - self.start_time
       
        B = B[0][1]

        self.t_measure_B[client] = numpy.append(self.t_measure_B[client] , t_measure)
        self.B_field[client] = numpy.append(self.B_field[client] , B['gauss'])

        self.do_fit_local(client)
        exe_str = "self.onNewSave" + client.replace(' ', '') + "('bfield')"
        exec exe_str

    @setting(15, "Set Measurements With Line Center", freq = '*(sv[MHz])', client = 's')
    def set_measurements_with_line_center(self, c, freq, client):
        '''
        takes the line center and sets up tracking
        Input i.e.: ([('line_center', U(-22.0, 'MHz'))], 'lattice')
        '''
        self.client_examination(client)
        t_measure = time.time() - self.start_time

        freq = freq[0][1]

        self.t_measure_line_center[client] = numpy.append(self.t_measure_line_center[client], t_measure)
        self.line_center[client] = numpy.append(self.line_center[client] , freq['MHz'])

        self.do_fit_local(client)
        exe_str = "self.onNewSave" + client.replace(' ', '') + "('linecenter')"
        exec exe_str

    @setting(4, "Get Clients", returns = '*s')
    def get_clients(self, c):
        '''Get all registered clients'''
        return client_list

    @setting(5, "Return Global or Local", boolean = 'b', client = 's')
    def return_global_or_local(self, c, boolean, client):
        '''
        Set the global or local auto-return boolean to be Ture or False
        Input i.e.: (True, 'lattice')
        '''
        self.bool_global[client] = boolean

    @setting(6, "Get Current Time", returns = 'v[min]')
    def get_current_time(self, c):
        '''Return current time which subtracts start time'''
        current_time = time.time() - self.start_time
        current_time = WithUnit(current_time, 's')
        return current_time.inUnitsOf('min')

    @setting(7, 'Remove B Measurement', point = 'i', client = 's')
    def remove_B_measurement(self, c, point, client):
        '''
        Removes the point w, can also be negative to count from the end
        Input i.e.: (0, 'lattice')
        '''
        self.client_examination(client)
        try:
            self.t_measure_B_nofit[client] = numpy.append(self.t_measure_B_nofit[client], self.t_measure_B[client][point])
            self.B_field_nofit[client] = numpy.append(self.B_field_nofit[client], self.B_field[client][point])
            self.t_measure_B[client] = numpy.delete(self.t_measure_B[client], point)
            self.B_field[client] = numpy.delete(self.B_field[client], point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit_local(client)

    @setting(8, 'Remove Line Center Measurement', point = 'i', client = 's')
    def remove_line_center_measurement(self, c, point, client):
        '''
        Removes the point w, can also be negative to count from the end
        Input i.e.: (0, 'lattice')
        '''
        self.client_examination(client)
        try:
            self.t_measure_line_center_nofit[client] = numpy.append(self.t_measure_line_center_nofit[client], self.t_measure_line_center[client][point])
            self.line_center_nofit[client] = numpy.append(self.line_center_nofit[client], self.line_center[client][point])
            self.t_measure_line_center[client] = numpy.delete(self.t_measure_line_center[client], point)
            self.line_center[client] = numpy.delete(self.line_center[client], point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit_local(client)

    @setting(9, 'Remove All Measurements', client = 's')
    def remove_all_measurements(self, c, client):
        '''
        Removes all measured data by a specified client
        Input i.e.: ('lattice')
        '''
        self.client_examination(client)
        self.t_measure_line_center_nofit[client] = numpy.append(self.t_measure_line_center_nofit[client], self.t_measure_line_center[client])
        self.line_center_nofit[client] = numpy.append(self.line_center_nofit[client], self.line_center[client])
        self.t_measure_B_nofit[client] = numpy.append(self.t_measure_B_nofit[client], self.t_measure_B[client])
        self.B_field_nofit[client] = numpy.append(self.B_field_nofit[client], self.B_field[client])
        self.t_measure_line_center[client] = numpy.array([])
        self.line_center[client] = numpy.array([])
        self.t_measure_B[client] = numpy.array([])
        self.B_field[client] = numpy.array([])
        self.do_fit_local(client)

    @setting(10, 'Get Fit History', client = 's', returns = '(*(v[s]v[gauss]) *(v[s]v[MHz]))')
    def get_fit_history(self, c, client):
        '''
        Get last local fit data points, including B field and line center
        Input i.e.: ('lattice')
        Return i.e.: ([(Value(58.58644199371338, 's'), Value(3.307939265053879, 'gauss')),
                       (Value(335.5155029296875, 's'), Value(3.307939265053879, 'gauss'))],
                      [(Value(58.58644199371338, 's'), Value(-21.578811982043565, 'MHz')),
                       (Value(335.5155029296875, 's'), Value(-21.578811982043565, 'MHz'))])
        '''
        self.client_examination(client)
        history_B = []
        history_line_center = []
        for t,b_field in zip(self.t_measure_B[client], self.B_field[client]):
            history_B.append((WithUnit(t,'s'),WithUnit(b_field,'gauss')))
        for t, freq in zip(self.t_measure_line_center[client], self.line_center[client]):
            history_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return [history_B, history_line_center]
    
    @setting(11, 'Get Excluded Points', client = 's', returns = '(*(v[s]v[gauss]) *(v[s]v[MHz]))')
    def get_excluded_points(self, c, client):
        '''
        Get excluded local fit data points, including B field and line center
        Input i.e.: ('lattice')
        Return i.e.: ([(Value(58.58644199371338, 's'), Value(3.307939265053879, 'gauss')),
                       (Value(335.5155029296875, 's'), Value(3.307939265053879, 'gauss'))],
                      [(Value(58.58644199371338, 's'), Value(-21.578811982043565, 'MHz')),
                       (Value(335.5155029296875, 's'), Value(-21.578811982043565, 'MHz'))])
        '''
        self.client_examination(client)
        excluded_B = []
        excluded_line_center = []
        for t,b_field in zip(self.t_measure_B_nofit[client], self.B_field_nofit[client]):
            excluded_B.append((WithUnit(t,'s'),WithUnit(b_field,'gauss')))
        for t, freq in zip(self.t_measure_line_center_nofit[client], self.line_center_nofit[client]):
            excluded_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return [excluded_B, excluded_line_center]

    @setting(12, "Get Lines From Bfield and Center", B = 'v[gauss]', freq = 'v[MHz]', returns = '*(sv[MHz])')
    def get_lines_from_bfield_and_center(self, c, B, freq):
        '''
        Input B field and line center, i.e.: (WithUnit(5.0, 'gauss'), WithUnit(-22.0, 'MHz'))
        Returns lines and frequencies, i.e.:[('S-1/2D-5/2', Value(-35.99419287374014, 'MHz')),
                                            ('S-1/2D-3/2', Value(-27.594108162862444, 'MHz')),
                                            ('S-1/2D-1/2', Value(-19.194023451984748, 'MHz')),
                                            ('S-1/2D+1/2', Value(-10.793938741107052, 'MHz')),
                                            ('S-1/2D+3/2', Value(-2.393854030229356, 'MHz')),
                                            ('S+1/2D-3/2', Value(-41.606145969770644, 'MHz')),
                                            ('S+1/2D-1/2', Value(-33.206061258892944, 'MHz')),
                                            ('S+1/2D+1/2', Value(-24.805976548015252, 'MHz')),
                                            ('S+1/2D+3/2', Value(-16.405891837137556, 'MHz')),
                                            ('S+1/2D+5/2', Value(-8.005807126259862, 'MHz'))]
        '''
        all_lines = self.tr.get_transition_energies(B, freq)
        return all_lines
    
    @setting(30, "Get Fit Parameters Local", name = 's', client = 's', returns = '?')
    def get_fit_parameters_local(self, c, name, client):
        '''
        returns the parameters for the latest local fit, name can be linecenter or bfield
        Input i.e.: ('linecenter', 'lattice') or ('bfield', 'lattice')
        Returns i.e.: DimensionlessArray([  5.21549529e-18,  -2.15788120e+01]) or None
        '''
        self.client_examination(client)
        if name == 'linecenter':
            fit = self.line_center_fit_local[client]
        elif name =='bfield':
            fit = self.B_fit_local[client]
        else:
            raise Exception("Provided name or client not found")
        if fit is not None:
            return fit
        else:
            return None

    @setting(31, "Get Fit Line Center Global", client = 's', returns = '?')
    def get_fit_line_center_global(self, c, client):
        '''
        returns the parameters for the latest global line center fit
        Input i.e.: ('lattice')
        Returns i.e.: DimensionlessArray([  2.35051007e-03,  -2.23465187e+01]) or None
        '''
        self.client_examination(client)
        fit = self.line_center_fit_global[client]
        if fit is not None:
            return fit
        else:
            return None
    
    @setting(40, "Get Current Lines local", client = 's', returns = '*(sv[MHz])')
    def get_current_lines_local(self, c, client):
        '''
        get the frequency of all current lines calculated by local fit parmeters
        Input i.e.: ('lattice')
        Returns i.e.: [('S-1/2D-5/2', Value(-30.837199999999978, 'MHz')),
                       ('S-1/2D-3/2', Value(-25.279805991021753, 'MHz')),
                       ('S-1/2D-1/2', Value(-19.722411982043525, 'MHz')),
                       ('S-1/2D+1/2', Value(-14.165017973065297, 'MHz')),
                       ('S-1/2D+3/2', Value(-8.607623964087065, 'MHz')),
                       ('S+1/2D-3/2', Value(-34.54999999999998, 'MHz')),
                       ('S+1/2D-1/2', Value(-28.992605991021755, 'MHz')),
                       ('S+1/2D+1/2', Value(-23.435211982043526, 'MHz')),
                       ('S+1/2D+3/2', Value(-17.877817973065298, 'MHz')),
                       ('S+1/2D+5/2', Value(-12.320423964087073, 'MHz'))]
        '''
        self.client_examination(client)
        lines = []
        current_time = time.time() - self.start_time
        try:
            B = self.fitter.evaluate(current_time, self.B_fit_local[client])
            center = self.fitter.evaluate(current_time, self.line_center_fit_local[client])
            #print 'try worked'
        except TypeError:
            # print 'exception coming'
            raise Exception ("Fit is not available")
        B = WithUnit(B, 'gauss')
        center = WithUnit(center, 'MHz')
        result = self.tr.get_transition_energies(B, center)
        #print 'heres the result'
        #print result
        for name,freq in result:
            lines.append((name, freq))
        return lines

    @setting(41, "Get Current Lines Global", client = 's', returns = '*(sv[MHz])')
    def get_current_lines_global(self, c, client):
        '''
        get the frequency of all current lines calculated by global fit parameters
        Input i.e.: ('lattice')
        Returns i.e.: [('S-1/2D-5/2', Value(-30.837199999999978, 'MHz')),
                       ('S-1/2D-3/2', Value(-25.279805991021753, 'MHz')),
                       ('S-1/2D-1/2', Value(-19.722411982043525, 'MHz')),
                       ('S-1/2D+1/2', Value(-14.165017973065297, 'MHz')),
                       ('S-1/2D+3/2', Value(-8.607623964087065, 'MHz')),
                       ('S+1/2D-3/2', Value(-34.54999999999998, 'MHz')),
                       ('S+1/2D-1/2', Value(-28.992605991021755, 'MHz')),
                       ('S+1/2D+1/2', Value(-23.435211982043526, 'MHz')),
                       ('S+1/2D+3/2', Value(-17.877817973065298, 'MHz')),
                       ('S+1/2D+5/2', Value(-12.320423964087073, 'MHz'))]
        '''
        self.client_examination(client)
        lines = []
        current_time = time.time() - self.start_time
        try:
            B = self.fitter.evaluate(current_time, self.B_fit_local[client])
            center = self.fitter.evaluate(current_time, self.line_center_fit_global[client])
            #print 'try worked'
        except TypeError:
            # print 'exception coming'
            raise Exception ("Fit is not available")
        B = WithUnit(B, 'gauss')
        center = WithUnit(center, 'MHz')
        result = self.tr.get_transition_energies(B, center)
        #print 'heres the result'
        #print result
        for name,freq in result:
            lines.append((name, freq))
        return lines

    @setting(42, "Get Current Lines", client = 's', returns = '*(sv[MHz])')
    def get_current_lines(self, c, client):
        '''
        Automatically detect whether to return global lines or local lines
        Input i.e.: ('lattice')
        Returns i.e.: [('S-1/2D-5/2', Value(-30.837199999999978, 'MHz')),
                       ('S-1/2D-3/2', Value(-25.279805991021753, 'MHz')),
                       ('S-1/2D-1/2', Value(-19.722411982043525, 'MHz')),
                       ('S-1/2D+1/2', Value(-14.165017973065297, 'MHz')),
                       ('S-1/2D+3/2', Value(-8.607623964087065, 'MHz')),
                       ('S+1/2D-3/2', Value(-34.54999999999998, 'MHz')),
                       ('S+1/2D-1/2', Value(-28.992605991021755, 'MHz')),
                       ('S+1/2D+1/2', Value(-23.435211982043526, 'MHz')),
                       ('S+1/2D+3/2', Value(-17.877817973065298, 'MHz')),
                       ('S+1/2D+5/2', Value(-12.320423964087073, 'MHz'))]
        '''
        if self.bool_global[client]:
            lines = yield self.get_current_lines_global(c, client)
        else:
            lines = yield self.get_current_lines_local(c, client)
        returnValue(lines)
    
    @setting(50, "Get Current Line Local", name = 's', client = 's', returns = 'v[MHz]')
    def get_current_line_local(self, c, name, client):
        '''
        Get the frequency of the current line specified by name and calculated by local fit parameters
        Input i.e.: ('S-1/2D-5/2'. 'lattice')
        Returns i.e.: Value(-30.837200000000003, 'MHz')
        '''
        self.client_examination(client)
        lines = yield self.get_current_lines_local(c, client)
        d = dict(lines)
##        print 'done getting lines'
##        print d.keys()
##        temp = WithUnit(1.0,'MHz')
##        yield temp
##        return
##        try:
##            yield d[name]
##            return
##        except KeyError:
##            raise Exception("Requested line not found")
        #print d.makeReport()
        try:
            #return d[name]
            returnValue(d[name])
        except KeyError:
            raise Exception ("Requested line not found")

    @setting(51, "Get Current Line Global", name = 's', client = 's', returns = 'v[MHz]')
    def get_current_line_global(self, c, name, client):
        '''
        Get the frequency of the current line specified by name and calculated by global fit parameters
        Input i.e.: ('S-1/2D-5/2'. 'lattice')
        Returns i.e.: Value(-30.837200000000003, 'MHz')
        '''
        self.client_examination(client)
        lines = yield self.get_current_lines_global(c, client)
        d = dict(lines)
##        print 'done getting lines'
##        print d.keys()
##        temp = WithUnit(1.0,'MHz')
##        yield temp
##        return
##        try:
##            yield d[name]
##            return
##        except KeyError:
##            raise Exception("Requested line not found")
        #print d.makeReport()
        try:
            #return d[name]
            returnValue(d[name])
        except KeyError:
            raise Exception ("Requested line not found")

    @setting(52, "Get Current Line", name = 's', client = 's', returns = 'v[MHz]')
    def get_current_line(self, c, name, client):
        '''
        Automatically detect whether to return global line or local line specified by name
        Input i.e.: ('S-1/2D-5/2'. 'lattice')
        Returns i.e.: Value(-30.837200000000003, 'MHz')
        '''
        if self.bool_global[client]:
            line = yield self.get_current_line_global(c, name, client)
        else:
            line = yield self.get_current_line_local(c, name, client)
        returnValue(line)
    
    @setting(60, "Get Current B Local", client = 's', returns = 'v[gauss]')
    def get_current_b_local(self, c, client):
        '''
        Get current b field calculated by local fit parameters (global fit is not applicable)
        Input i.e.: ('lattice')
        Returns i.e.: Value(3.307939265053879, 'gauss')
        '''
        self.client_examination(client)
        current_time = time.time() - self.start_time
        try:
            B = self.fitter.evaluate(current_time, self.B_fit_local[client])
            B = WithUnit(B, 'gauss')
        except TypeError:
            # print 'exception coming'
            raise Exception ("Fit is not available")
        return B
        #returnValue(B)
        
    @setting(70, "Get Current Center Local", client = 's', returns = 'v[MHz]')
    def get_current_center_local(self, c, client):
        '''
        Get current line center calculated by local fit parameters
        Input i.e.: ('lattice')
        Returns i.e.: Value(-21.578811982043565, 'MHz')
        '''
        self.client_examination(client)
        current_time = time.time() - self.start_time
        try:
            center = self.fitter.evaluate(current_time, self.line_center_fit_local[client])
            center = WithUnit(center, 'MHz')
        except TypeError:
            # print 'exception coming'
            raise Exception ("Fit is not available")
        return center
        #returnValue(center)

    @setting(71, "Get Current Center Global", client = 's', returns = 'v[MHz]')
    def get_current_center_global(self, c, client):
        '''
        Get current line center calculated by global fit parameters
        Input i.e.: ('lattice')
        Returns i.e.: Value(-21.578811982043565, 'MHz')
        '''
        self.client_examination(client)
        current_time = time.time() - self.start_time
        try:
            center = self.fitter.evaluate(current_time, self.line_center_fit_global[client])
            center = WithUnit(center, 'MHz')
        except TypeError:
            # print 'exception coming'
            raise Exception ("Fit is not available")
        return center
        #returnValue(center)

    @setting(72, "Get Current Center", client = 's', returns = 'v[MHz]')
    def get_current_center(self, c, client):
        '''
        Automatically detect whether to return global line center or local line center
        Input i.e.: ('lattice')
        Returns i.e.: Value(-21.578811982043565, 'MHz')
        '''
        if self.bool_global[client]:
            center = yield self.get_current_center_global(c, client)
        else:
            center = yield self.get_current_center_local(c, client)
        returnValue(center)
    
    @setting(80, 'History Duration Local', client = 's', duration = '*v[s]', returns = '*v[s]')
    def get_history_duration_local(self, c, client, duration = None):
        '''
        Get tracking durations for local B field and line center if duration == None
        Input i.e.: ('lattice')
        Returns i.e.: ValueArray(array([ 6000.,  6000.]), 's')

        Set tracking durations for local B field and line center if duration != None
        Input i.e.: ('lattice', (WithUnit(7000, 's'), WithUnit(7000, 's')))
        Returns i.e.: ValueArray(array([ 7000.,  7000.]), 's')
        '''
        self.client_examination(client)
        if duration is not None:
            self.keep_B_measurements_local[client] = duration[0]['s']
            self.keep_line_center_measurements_local[client] = duration[1]['s']
            self.do_fit_local(client)
        return [ WithUnit(self.keep_B_measurements_local[client],'s'), WithUnit(self.keep_line_center_measurements_local[client], 's') ]

    @setting(81, 'History Duration Global Line Center', client = 's', duration = 'v[s]', returns = 'v[s]')
    def get_history_duration_global_line_center(self, c, client, duration = None):
        '''
        Get tracking durations for global line center if duration == None
        Input i.e.: ('lattice')
        Returns i.e.: Value(6000.0, 's')

        Set tracking durations for global line center if duration != None
        Input i.e.: ('lattice', WithUnit(7000, 's'))
        Returns i.e.: Value(7000.0, 's')
        '''
        self.client_examination(client)
        if duration is not None:
            self.keep_line_center_measurements_global[client] = duration['s']
            self.do_fit_local(client)
        return WithUnit(self.keep_line_center_measurements_global[client], 's')

    @setting(90, 'Get Last B Field Global', returns = 'v')
    def get_last_b_field_global(self, c):        
        ''' 
        Returns the last entered global B field
        Returns i.e.: 3.307939265053879
        '''
        B_field_global = self.arraydict_join(self.B_field)
        t_measure_B_global = self.arraydict_join(self.t_measure_B)
        last_index = numpy.where(t_measure_B_global == numpy.max(t_measure_B_global))
        return B_field_global[last_index]

    @setting(91, 'Get Last B Field Local', client = 's', returns = 'v')
    def get_last_b_field_local(self, c, client):        
        '''
        Returns the last entered local B field
        Input i.e.: ('lattice')
        Returns i.e.: 3.307939265053879
        '''
        self.client_examination(client)
        return self.B_field[client][-1]

    @setting(100, 'Get Last Line Center Global', returns = 'v')
    def get_last_line_center_global(self, c):
        '''
        Returns the last entered global line center
        Returns i.e.: -21.578811982043565
        '''
        line_center_global = self.arraydict_join(self.line_center)
        t_measure_line_center_global = self.arraydict_join(self.t_measure_line_center)
        last_index = numpy.where(t_measure_line_center_global == numpy.max(t_measure_line_center_global))
        return line_center_global[last_index]

    @setting(101, 'Get Last Line Center Local', client = 's', returns = 'v')
    def get_last_line_center_local(self, c, client):
        '''
        Returns the last entered local line center
        Input i.e.: ('lattice')
        Returns i.e.: -21.578811982043565
        '''
        self.client_examination(client)
        return self.line_center[client][-1]

    @setting(110, 'Get B Field Global', returns = '*(s*v)')
    def get_b_field_global(self, c):        
        '''
        Returns all entered B fields
        Returns i.e.: [('lattice', DimensionlessArray([ 3.30793927])),
                       ('sqip', DimensionlessArray([], dtype=float64)),
                       ('space time', DimensionlessArray([], dtype=float64)),
                       ('cct', DimensionlessArray([], dtype=float64))]
        '''
        return self.B_field.items()

    @setting(111, 'Get B Field Local', client = 's', returns = '*v')
    def get_b_field_local(self, c, client):        
        '''
        Returns the local B field
        Input i.e.: ('lattice')
        Returns i.e.: DimensionlessArray([ 3.30793927,  3.30793927])
        '''
        self.client_examination(client)
        return self.B_field[client]

    @setting(120, 'Get Line Center Global', returns = '*(s*v)')
    def get_line_center_global(self, c):
        '''
        Returns all entered line centers
        Returns i.e.: [('lattice', DimensionlessArray([-21.57881198, -21.57881198])),
                       ('sqip', DimensionlessArray([], dtype=float64)),
                       ('space time', DimensionlessArray([], dtype=float64)),
                       ('cct', DimensionlessArray([], dtype=float64))]
        '''
        return self.line_center.items()

    @setting(121, 'Get Line Center Local', client = 's', returns = '*v')
    def get_line_center_local(self, c, client):
        '''
        Returns the local line center
        Input i.e.: ('lattice')
        Returns i.e.: DimensionlessArray([-21.57881198, -21.57881198])
        '''
        self.client_examination(client)
        return self.line_center[client]

    @setting(122, 'Get Line Center Global Fit Data', client = 's', returns = '*(v[s]v[MHz])')
    def get_line_center_global_fit_data(self, c, client):
        '''
        Returns the global fit dataset regarding to last global line center fit parameters
        Input i.e.: ('lattice')
        Returns i.e.: [(Value(6106.04318189621, 's'), Value(-21.578811982043565, 'MHz')),
                       (Value(7915.106670856476, 's'), Value(-21.578811982043565, 'MHz'))]
        '''
        self.client_examination(client)
        history_global_line_center = []
        for t, freq in zip(self.t_measure_line_center_fit_global_data[client], self.line_center_fit_global_data[client]):
            history_global_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return history_global_line_center

    @setting(130, "Set Global Fit List", client = 's', fit_list = '*s')
    def set_global_fit_list(self, c, client, fit_list):
        '''
        Set global line center fit client list
        Input i.e.: ('lattice', ['cct', 'sqip', 'space time'])
        '''
        self.client_examination(client)
        for key in fit_list:
            if key not in client_list:
                raise Exception('{0} not in client list {1}'.format(key, client_list))
        self.global_fit_list[client] = fit_list
        self.do_fit_local(client)

    @setting(131, "Get Global Fit List", client = 's', returns = '*s')
    def get_global_fit_list(self, c, client):
        '''
        Get global line center fit client list
        Input i.e.: ('lattice')
        Returns i.e.: ['cct', 'sqip', 'space time']
        '''
        self.client_examination(client)
        return self.global_fit_list[client]

    def do_fit_global(self):
        '''
        Refresh data and fit parameters fot all clients
        '''

        for client in client_list:
            self.remove_old_measurements(client)
            if (len(self.t_measure_B[client])):
                self.B_fit_local[client] = self.fitter.fit(self.t_measure_B[client], self.B_field[client])
            else:
                self.B_fit_local[client] = None

            if (len(self.t_measure_line_center[client])):
                self.line_center_fit_local[client] = self.fitter.fit(self.t_measure_line_center[client], self.line_center[client])
            else:
                self.line_center_fit_local[client] = None

            line_center_global = self.arraydict_join(self.line_center, self.global_fit_list[client])
            t_measure_line_center_global = self.arraydict_join(self.t_measure_line_center, self.global_fit_list[client])
                
            keep_line_center = numpy.where((self.current_time - t_measure_line_center_global) < self.keep_line_center_measurements_global[client])
            self.line_center_fit_global_data[client] = line_center_global[keep_line_center]
            self.t_measure_line_center_fit_global_data[client] = t_measure_line_center_global[keep_line_center]
            if (len(self.t_measure_line_center_fit_global_data[client])):
                self.line_center_fit_global[client] = self.fitter.fit(self.t_measure_line_center_fit_global_data[client], self.line_center_fit_global_data[client])
            else:
                self.line_center_fit_global[client] = None
        
        if (time.time() - self.start_time) > clear_all_duration:
            t_measure_line_center_all = self.arraydict_join(self.t_measure_line_center)
            t_measure_B_all = self.arraydict_join(self.t_measure_B)
            t_measure_all = numpy.append(t_measure_line_center_all, t_measure_B_all)
            try:
                t_measure_min = t_measure_all.min()
            except Exception as e:
                t_measure_min = clear_all_duration
            for client in client_list:
                self.t_measure_line_center[client] = self.t_measure_line_center[client] - t_measure_min
                self.t_measure_B[client] = self.t_measure_B[client] - t_measure_min
            self.t_measure_line_center_nofit = dict.fromkeys(client_list, numpy.array([]))
            self.t_measure_B_nofit = dict.fromkeys(client_list, numpy.array([]))
            self.line_center_nofit = dict.fromkeys(client_list, numpy.array([]))
            self.B_field_nofit = dict.fromkeys(client_list, numpy.array([]))
            self.start_time = self.start_time + t_measure_min
        
        self.onNewFit(None)

    def do_fit_local(self, client):
        '''
        Refresh data points and fit parameters for a client
        '''
        self.client_examination(client)

        self.remove_old_measurements(client)

        if (len(self.t_measure_B[client])):
            self.B_fit_local[client] = self.fitter.fit(self.t_measure_B[client], self.B_field[client])
        else:
            self.B_fit_local[client] = None

        if (len(self.t_measure_line_center[client])):
            self.line_center_fit_local[client] = self.fitter.fit(self.t_measure_line_center[client], self.line_center[client])
        else:
            self.line_center_fit_local[client] = None
        
        for key in client_list:
            line_center_global = self.arraydict_join(self.line_center, self.global_fit_list[key])
            t_measure_line_center_global = self.arraydict_join(self.t_measure_line_center, self.global_fit_list[key])
                
            keep_line_center = numpy.where((self.current_time - t_measure_line_center_global) < self.keep_line_center_measurements_global[key])
            self.line_center_fit_global_data[key] = line_center_global[keep_line_center]
            self.t_measure_line_center_fit_global_data[key] = t_measure_line_center_global[keep_line_center]
            if (len(self.t_measure_line_center_fit_global_data[key])):
                self.line_center_fit_global[key] = self.fitter.fit(self.t_measure_line_center_fit_global_data[key], self.line_center_fit_global_data[key])
            else:
                self.line_center_fit_global[key] = None
        self.onNewFit(None)
    
    def remove_old_measurements(self, client):
        '''
        Remove old data points for a client. Old data points exceed local tracking durations
        '''
        self.client_examination(client)

        self.current_time = time.time() - self.start_time

        keep_line_center = numpy.where( (self.current_time - self.t_measure_line_center[client]) < self.keep_line_center_measurements_local[client])
        keep_B = numpy.where( (self.current_time - self.t_measure_B[client]) < self.keep_B_measurements_local[client])

        self.t_measure_line_center[client] = self.t_measure_line_center[client][keep_line_center]
        self.t_measure_B[client] = self.t_measure_B[client][keep_B]
        self.B_field[client] = self.B_field[client][keep_B]
        self.line_center[client] = self.line_center[client][keep_line_center]

if __name__ == '__main__':
    from labrad import util
    util.runServer(SDTrackerGlobal())
