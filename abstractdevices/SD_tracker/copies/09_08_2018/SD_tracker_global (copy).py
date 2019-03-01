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
import time
from SD_tracker_config import config as conf
from SD_calculator import Transitions_SD, fitter
import numpy
#from labrad.units import WithUnit

client_list = ['lattice', 'cct', 'sqip', 'space time']
keep_line_center_measurements_local = dict.fromkeys(client_list, 100*60)
keep_line_center_measurements_global = dict.fromkeys(client_list, 100*60)
keep_B_measurements_local = dict.fromkeys(client_list, 100*60)

class SDTrackerGlobal(LabradServer):
    """Provides ability to track drifts of the SD line"""
    name = 'SD Tracker Global'
    
    onNewFit = Signal( 768120, 'signal: new fit', '' )
    
    @inlineCallbacks
    def initServer(self):
        self.start_time = time.time()
        self.keep_line_center_measurements_local = keep_line_center_measurements_local
        self.keep_line_center_measurements_global = keep_line_center_measurements_global
        self.keep_B_measurements_local = keep_B_measurements_local
        self.tr = Transitions_SD()
        self.fitter = fitter()
        self.t_measure_line_center = dict.fromkeys(client_list, numpy.array([]))
        self.t_measure_B = dict.fromkeys(client_list, numpy.array([]))
        self.t_measure_line_center_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.t_measure_B_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.line_center = dict.fromkeys(client_list, numpy.array([]))
        self.line_center_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.B_field = dict.fromkeys(client_list, numpy.array([]))
        self.B_field_nofit = dict.fromkeys(client_list, numpy.array([]))
        self.line_center_fit_local = dict.fromkeys(client_list)
        self.B_fit_local = dict.fromkeys(client_list)
        self.line_center_fit_global = dict.fromkeys(client_list)
        self.t_measure_line_center_fit_global_data = dict.fromkeys(client_list, numpy.array([]))
        self.line_center_fit_global_data = dict.fromkeys(client_list, numpy.array([]))
        self.global_fit_list = dict.fromkeys(client_list)
        self.bool_global = dict.fromkeys(client_list, False)
        self.dv = {}
        yield self.connect_data_vault()
        yield self.setupListeners()
    
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
            yield self.dv.add((t_measure, freq, b_field, client))
        except AttributeError:
            print 'Data Vault Not Available, not saving'
            yield None

    def arraydict_join(self, dic, key_list = None):
        array = numpy.array([])
        if key_list:
            for key in key_list:
                if key not in dic.keys():
                    raise Exception('{0} not in {1}'.format(key, dic.keys()))
                elif type(dic[key]) == numpy.ndarray:
                    array = numpy.append(array, dic[key])
                else:
                    raise Exception('Value type in dictionary is not numpy.ndarray.')
        return array

    def client_examination(self, client):
        if client not in client_list:
            raise Exception("{0} not in client list: {1}".format(client, client_list))
        else:
            pass
    
    @setting(1, 'Get Transition Names', returns = '*s')
    def get_transitions(self, c):
        '''Returns the names of possible transitions'''
        return self.tr.transitions()
        
    @setting(2, 'Set Measurements', lines = '*(sv[MHz])', client = 's', returns = '')
    def set_measurements(self, c, lines, client):
        '''takes the names and frequencies of two lines and performs tracking'''
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
        yield self.save_result_datavault(time.time(), freq['MHz'], B['gauss'], client)
        self.do_fit(client)

    @setting(3, 'Set Measurements with Bfield and Line Center', B = '*(sv[gauss])', freq = '*(sv[MHz])', client = 's', returns = '')
    def set_measurements_with_bfield_and_line_center(self, c, B, freq, client):
        '''takes the Bfield and the line center and sets up tracking'''
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
        yield self.save_result_datavault(time.time(), freq['MHz'], B['gauss'], client)
        self.do_fit(client)
    
    #@setting(12, 'Set Measurement One Line', line = 'sv[MHz]', client = 's', returns = '')
    #def set_measurement_one_line(self, c, line, client):
    #    ''' takes name and frequency of one line, and assumes the cavity position from previous data '''
    #    t_measure = time.time() - self.start_time
    #    name,f = line
    #    if name not in self.tr.transitions():
    #        raise Exception("Line does not match a known transition")

    @setting(4, "Get Clients", returns = '*s')
    def get_clients(self, c):
        return client_list

    @setting(5, "Return Global or Local", boolean = 'b', client = 's')
    def return_global_or_local(self, c, boolean, client):
        self.bool_global[client] = boolean

    @setting(6, "Get Current Time", returns = 'v[min]')
    def get_current_time(self, c):
        current_time = time.time() - self.start_time
        current_time = WithUnit(current_time, 's')
        return current_time.inUnitsOf('min')
    
    @setting(30, "Get Fit Parameters Local", name = 's', client = 's', returns = '?')
    def get_fit_parameters_local(self, c, name, client):
        '''returns the parameters for the latest fit, name can be linecenter or bfield'''
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
        '''returns the parameters for the latest line center fit'''
        self.client_examination(client)
        fit = self.line_center_fit_global[client]
        if fit is not None:
            return fit
        else:
            return None
    
    @setting(40, "Get Current Lines local", client = 's', returns = '*(sv[MHz])')
    def get_current_lines_local(self, c, client):
        '''get the frequency of the current line specified by name. if name is not provided, get all lines'''
        self.client_examination(client)
        lines = []
        current_time = time.time() - self.start_time
        try:
            B = self.fitter.evaluate(current_time, self.B_fit_local[client])
            center = self.fitter.evaluate(current_time, self.line_center_fit_local[client])
            #print 'try worked'
        except TypeError:
            print 'exception coming'
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
        '''get the frequency of the current line specified by name. if name is not provided, get all lines'''
        self.client_examination(client)
        lines = []
        current_time = time.time() - self.start_time
        try:
            B = self.fitter.evaluate(current_time, self.B_fit_local[client])
            center = self.fitter.evaluate(current_time, self.line_center_fit_global[client])
            #print 'try worked'
        except TypeError:
            print 'exception coming'
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
        if self.bool_global[client]:
            lines = yield self.get_current_lines_global(c, client)
        else:
            lines = yield self.get_current_lines_local(c, client)
        returnValue(lines)
    
    @setting(50, "Get Current Line Local", name = 's', client = 's', returns = 'v[MHz]')
    def get_current_line_local(self, c, name, client):
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
        if self.bool_global[client]:
            line = yield self.get_current_line_global(c, name, client)
        else:
            line = yield self.get_current_line_local(c, name, client)
        returnValue(line)
    
    @setting(60, "Get Current B Local", client = 's', returns = 'v[gauss]')
    def get_current_b_local(self, c, client):
        self.client_examination(client)
        current_time = time.time() - self.start_time
        B = self.fitter.evaluate(current_time, self.B_fit_local[client])
        B = WithUnit(B, 'gauss')
        return B
        #returnValue(B)
        
    @setting(70, "Get Current Center Local", client = 's', returns = 'v[MHz]')
    def get_current_center_local(self, c, client):
        self.client_examination(client)
        current_time = time.time() - self.start_time
        center = self.fitter.evaluate(current_time, self.line_center_fit_local[client])
        center = WithUnit(center, 'MHz')
        return center
        #returnValue(center)

    @setting(71, "Get Current Center Global", client = 's', returns = 'v[MHz]')
    def get_current_center_global(self, c, client):
        self.client_examination(client)
        current_time = time.time() - self.start_time
        center = self.fitter.evaluate(current_time, self.line_center_fit_global[client])
        center = WithUnit(center, 'MHz')
        return center
        #returnValue(center)

    @setting(72, "Get Current Center", client = 's', returns = 'v[MHz]')
    def get_current_center(self, c, client):
        if self.bool_global[client]:
            center = yield self.get_current_center_global(c, client)
        else:
            center = yield self.get_current_center_local(c, client)
        returnValue(center)
    
    @setting(10, 'Remove B Measurement', point = 'i', client = 's')
    def remove_B_measurement(self, c, point, client):
        '''removes the point w, can also be negative to count from the end'''
        self.client_examination(client)
        try:
            self.t_measure_B_nofit[client] = numpy.append(self.t_measure_B_nofit[client], self.t_measure_B[client][point])
            self.B_field_nofit[client] = numpy.append(self.B_field_nofit[client], self.B_field[client][point])
            self.t_measure_B[client] = numpy.delete(self.t_measure_B[client], point)
            self.B_field[client] = numpy.delete(self.B_field[client], point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit(client)

    @setting(11, 'Remove Line Center Measurement', point = 'i', client = 's')
    def remove_line_center_measurement(self, c, point, client):
        '''removes the point w, can also be negative to count from the end'''
        self.client_examination(client)
        try:
            self.t_measure_line_center_nofit[client] = numpy.append(self.t_measure_line_center_nofit[client], self.t_measure_line_center[client][point])
            self.line_center_nofit[client] = numpy.append(self.line_center_nofit[client], self.line_center[client][point])
            self.t_measure_line_center[client] = numpy.delete(self.t_measure_line_center[client], point)
            self.line_center[client] = numpy.delete(self.line_center[client], point)
        except ValueError or IndexError:
            raise Exception("Point not found")
        self.do_fit(client)

    @setting(8, 'Get Fit History', client = 's', returns = '(*(v[s]v[gauss]) *(v[s]v[MHz]))')
    def get_fit_history(self, c, client):
        self.client_examination(client)
        history_B = []
        history_line_center = []
        for t,b_field in zip(self.t_measure_B[client], self.B_field[client]):
            history_B.append((WithUnit(t,'s'),WithUnit(b_field,'gauss')))
        for t, freq in zip(self.t_measure_line_center[client], self.line_center[client]):
            history_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return [history_B, history_line_center]
    
    @setting(14, 'Get Excluded Points', client = 's', returns = '(*(v[s]v[gauss]) *(v[s]v[MHz]))')
    def get_excluded_points(self, c, client):
        self.client_examination(client)
        excluded_B = []
        excluded_line_center = []
        for t,b_field in zip(self.t_measure_B_nofit[client], self.B_field_nofit[client]):
            excluded_B.append((WithUnit(t,'s'),WithUnit(b_field,'gauss')))
        for t, freq in zip(self.t_measure_line_center_nofit[client], self.line_center_nofit[client]):
            excluded_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return [excluded_B, excluded_line_center]
    
    @setting(80, 'History Duration Local', client = 's', duration = '*v[s]', returns = '*v[s]')
    def get_history_duration_local(self, c, client, duration = None):
        self.client_examination(client)
        if duration is not None:
            self.keep_B_measurements_local[client] = duration[0]['s']
            self.keep_line_center_measurements_local[client] = duration[1]['s']
            self.do_fit(client)
        return [ WithUnit(self.keep_B_measurements_local[client],'s'), WithUnit(self.keep_line_center_measurements_local[client], 's') ]

    @setting(81, 'History Duration Global Line Center', client = 's', duration = 'v[s]', returns = 'v[s]')
    def get_history_duration_global_line_center(self, c, client, duration = None):
        self.client_examination(client)
        if duration is not None:
            self.keep_line_center_measurements_global[client] = duration['s']
            self.do_fit(client)
        return WithUnit(self.keep_line_center_measurements_global[client], 's')

    @setting(90, 'Get Last B Field Global', returns = 'v')
    def get_last_b_field_global(self, c):        
        ''' returns the last entered global B field '''
        B_field_global = self.arraydict_join(self.B_field, client_list)
        t_measure_B_global = self.arraydict_join(self.t_measure_B, client_list)
        last_index = numpy.where(t_measure_B_global == numpy.max(t_measure_B_global))
        return B_field_global[last_index]

    @setting(91, 'Get Last B Field Local', client = 's', returns = 'v')
    def get_last_b_field_local(self, c, client):        
        ''' returns the last entered local B field '''
        self.client_examination(client)
        return self.B_field[client][-1]

    @setting(100, 'Get Last Line Center Global', returns = 'v')
    def get_last_line_center_global(self, c):
        ''' returns the last entered global line center '''
        line_center_global = self.arraydict_join(self.line_center, client_list)
        t_measure_line_center_global = self.arraydict_join(self.t_measure_line_center, client_list)
        last_index = numpy.where(t_measure_line_center_global == numpy.max(t_measure_line_center_global))
        return line_center_global[last_index]

    @setting(101, 'Get Last Line Center Local', client = 's', returns = 'v')
    def get_last_line_center_local(self, c, client):
        ''' returns the last entered local line center '''
        self.client_examination(client)
        return self.line_center[client][-1]

    @setting(110, 'Get B Field Global', returns = '?')
    def get_b_field_global(self, c):        
        ''' returns all entered B fields '''
        return self.B_field.items()

    @setting(111, 'Get B Field Local', client = 's', returns = '*v')
    def get_b_field_local(self, c, client):        
        ''' returns the local B field '''
        self.client_examination(client)
        return self.B_field[client]

    @setting(120, 'Get Line Center Global', returns = '?')
    def get_line_center_global(self, c):
        ''' returns all entered line centers '''
        return self.line_center.items()

    @setting(121, 'Get Line Center Local', client = 's', returns = '*v')
    def get_line_center_local(self, c, client):
        ''' returns the local line center '''
        self.client_examination(client)
        return self.line_center[client]

    @setting(122, 'Get Line Center Global Fit Data', client = 's', returns = '*(v[s]v[MHz])')
    def get_line_center_global_fit_data(self, c, client):
        self.client_examination(client)
        history_global_line_center = []
        for t, freq in zip(self.t_measure_line_center_fit_global_data[client], self.line_center_fit_global_data[client]):
            history_global_line_center.append((WithUnit(t,'s'), WithUnit(freq, 'MHz')))
        return history_global_line_center

    @setting(18, "Get Lines From Bfield and Center", B = 'v[gauss]', freq = 'v[MHz]', returns = '*(sv[MHz])')
    def get_lines_from_bfield_and_center(self, c, B, freq):
        all_lines = self.tr.get_transition_energies(B, freq)
        return all_lines

    @setting(131, "Set Global Fit List", client = 's', fit_list = '*s')
    def set_global_fit_list(self, c, client, fit_list):
        self.client_examination(client)
        for key in fit_list:
            if key not in client_list:
                raise Exception('{0} not in client list {0}'.format(key, client_list))
        self.global_fit_list[client] = fit_list
        self.do_fit(client)

    @setting(141, "Get Global Fit List", client = 's', returns = '?')
    def get_global_fit_list(self, c, client):
        self.client_examination(client)
        return self.global_fit_list[client]

    def do_fit(self, client):
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
