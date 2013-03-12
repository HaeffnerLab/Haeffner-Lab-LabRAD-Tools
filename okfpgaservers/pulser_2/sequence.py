from hardwareConfiguration import hardwareConfiguration
from userConfiguration import user_configuration
import numpy as np
from decimal import Decimal

durationAdvance = 2 #duration of the 'adance' TTL pulse in pulser timesteps
minPulseLengthTTL = durationAdvance
minPulseLengthDDS = 2 * durationAdvance
minPulseGapOnFreqChange = 150 #timesteps, which is 6 microseconds

#ttl parsing
#max ttl switches
#new gui for swtiches (no auto), dds

#defining pulse classes
class pulse(object):
    def __init__(self, channel, start, end):
        self.channel = channel
        self.start = start
        self.end = end

class dds_pulse(pulse):
    def __init__(self, channel, start, end, freq, ampl, phase):
        super(dds_pulse, self).__init__(channel, start, end)
        self.pulse_type = 'dds'
        self.freq = freq
        self.ampl = ampl
        self.off_ampl = user_configuration.dds_channels[channel].off_amplitude
        self.phase = phase
    
    @property
    def setting(self):
        return (self.freq, self.ampl, self.phase)
    
    @property
    def off_setting(self):
        return (self.freq, self.off_ampl , self.phase)

class ttl_pulse(pulse):
    def __init__(self, channel, start, end):
        super(ttl_pulse, self).__init__(channel, start, end)
        self.pulse_type = 'ttl'

class Sequence():
    """Sequence for programming pulses"""
    def __init__(self, parent):
        self.parent = parent
        self.channelTotal = hardwareConfiguration.channelTotal
        self.timeResolution = Decimal(hardwareConfiguration.timeResolution)
        self.advanceDDS = user_configuration.ttl_channels['AdvanceDDS'].channelnumber
        self.resetDDS = user_configuration.ttl_channels['ResetDDS'].channelnumber
        self.dds_dict = {}
        
    def add_dds_pulse(self, channel, start, stop, frequency, amplitude, phase):
        if start == stop: return# zero length pulses are ignored
        start = self.secToStep(start)
        stop = self.secToStep(stop)
        pulse = dds_pulse(channel, start, stop, frequency, amplitude, phase)
        try:
            self.dds_dict[channel].append(pulse)
        except KeyError:
            self.dds_dict[channel] = [pulse]
    
    def secToStep(self, sec):
        '''converts seconds to time steps'''
        start = '{0:.9f}'.format(sec) #round to nanoseconds
        start = Decimal(start) #convert to decimal 
        step = ( start / self.timeResolution).to_integral_value()
        step = int(step)
        return step
    
    def pulse_type_limits(self, pulse):
        '''
        returns the limits on duration for dds and tll pulses
        '''
        if pulse.pulse_type == 'dds':
            minPulseLength = minPulseLengthDDS
            minGapNoChange = minPulseLengthDDS
            minGapOnChange = (minPulseGapOnFreqChange, minPulseLengthDDS, minPulseLengthDDS)
        elif pulse.pulse_type == 'ttl':
            minPulseLength = minPulseLengthTTL
            minGapOnChange = minPulseLengthTTL
            minGapNoChange = (minPulseLengthTTL, )
        return minPulseLength, minGapOnChange, minGapNoChange
    
    def check_errors(self, last_pulse, new_pulse):
        minPulseLength, minGapOnChange, minGapNoChange = self.pulse_type_limits(last_pulse)
        difference = new_pulse.start - last_pulse.end
        message_collision=''
        message_duration=''
        if difference < 0:
            message_collision = "Overlap found at {0} channel {1}. Pulse starting at {2} but previous ending at {3}"
        elif last_pulse.setting == new_pulse.setting and difference < minGapNoChange:
            message_collision = "Gap Between Pulses Too Short for {0} channel {1}. Pulse starting at {2} but previous ending at {3}"
        else:
            #check on errors if any of the settings were changed
            for i,last_setting in enumerate(last_pulse.setting):
                if new_pulse.setting[i] != last_setting and difference < minGapOnChange[i]:
                    message_collision = "Gap Between Pulses Too Short for {0} channel {1}. Pulse starting at {2} but previous ending at {3}"
        #check for duration erros of each pulse
        for p in [last_pulse, new_pulse]:
            if p.start < minPulseLength:
                message_duration = "Pulse starts too early for {0} channel {1}, starting at {2}"
                message_duration = message_duration.format(p.pulse_type, p.channel, p.start)
            if p.end - p.start < minPulseLength:
                message_duration = "Pulse is too short for {0} channel {1}, starting at {2}, ending at {3}"
                message_duration = message_duration.format(p.pulse_type, p.channel, p.start, p.end)
            if p.end > hardwareConfiguration.max_pulse_duration:
                message_duration = "Pulse sequence is too long, exceeded by {0} channel {1} at time {2}".format(p.pulse_type, p.channel, p.end)
        #format and raise the relevant error message
        message = '' 
        if message_collision:
            message = message_collision.format(new_pulse.pulse_type, new_pulse.channel, new_pulse.start, last_pulse.end)
        if message_duration:
            message = message_duration
        if message:
            raise Exception (message)
    
    def merge_adjacent(self, pulse_list):
        '''
        merges adjacent dds pulses by combining pulses together when they are back to back and have the same dds settings
        '''
        merged = []
        pulses_sorted_by_start = sorted(pulse_list, key = lambda pulse: pulse.start)
        if not pulses_sorted_by_start: return merged
        last_pulse = pulses_sorted_by_start.pop(0)
        while pulses_sorted_by_start:
            pulse = pulses_sorted_by_start.pop(0)
            if last_pulse.end == pulse.start and last_pulse.setting == pulse.setting:
                last_pulse.end = pulse.end
            else:
                self.check_errors(last_pulse, pulse)
                merged.append(last_pulse)
                last_pulse = pulse
        merged.append(last_pulse)
        return merged
    
    def get_merged_pulses(self):
        '''returns all pulses while mergent adjacent pulses for each channel'''
        all_pulses = []
        for pulse_list in self.dds_dict.itervalues():
            merged = self.merge_adjacent(pulse_list)
            all_pulses.extend(merged)
        return all_pulses
    
    def convert_to_edges(self, pulses):
        '''
        converts dds pulses to edges sorted
        '''
        edges = []
        channels = []
        for pulse in pulses:
            channels.append(pulse.channel)
            edges.append((pulse.start, pulse.channel, pulse.setting))
            edges.append((pulse.end, pulse.channel, pulse.off_setting))
        sorted_edges = sorted(edges)
        sorted_times = [edge[0] for edge in sorted_edges]
        #checking for adjacent edges conflicts
        time_differences = np.diff(sorted_times)
        correct_spacing = (0 == time_differences) | (time_differences >= minPulseLengthDDS)
        if not correct_spacing.all():
            arg = np.argwhere(correct_spacing == False)[0][0]
            raise Exception("Two pulse edges are too close together: channels {0} and {1} at time {2} sec".
                format(sorted_edges[arg][1], sorted_edges[arg + 1][1], sorted_edges[arg][0] * float(self.timeResolution)))
        #checking for maximum number of edges
        if len(set(sorted_times)) > hardwareConfiguration.max_dds_edges:
            raise Exception ("Too many DDS Edges in the pulse sequence")
        channels = list(set(channels))
        return sorted_edges, channels
     
    def _get_edges_with_next_duration_dds(self, edges):
        '''
        returns all the edges with the next duration in the format {channel:num}
        '''
        next = {}
        next_time = edges[0][0]
        while True:
            try:
                belongs = next_time == edges[0][0]
                if belongs:
                    next_edge = edges.pop(0)
                    start,channel_name,(frequency,amplitude, phase) = next_edge
                    channel = user_configuration.dds_channels[channel_name]
                    next[channel_name] = self.parent._valToInt_coherent(channel, True, frequency, amplitude, phase)
                else:
                    break
            except IndexError:
                break
        return next_time, next
    
    def parse_dds(self):
        '''
        state starts out in the initial state and then get updated by the pulse edges
        '''
        all_pulses = self.get_merged_pulses()
        sorted_edges, used_channels = self.convert_to_edges(all_pulses)
        state = self.parent._getCurrentDDS(used_channels)
        dds_program = {}.fromkeys(state, '')
        self.add_to_dds_program(dds_program, state)
        while sorted_edges:
            next_time, next_edges = self._get_edges_with_next_duration_dds(sorted_edges)
            state.update(next_edges)
            self.add_to_dds_program(dds_program, state)
            self.add_advance_dds(next_time)
        #add termination
        for name in dds_program.iterkeys():
            dds_program[name] +=  '\x00\x00'
        return dds_program
    
    def add_advance_dds(self, timestep):
        pass
    
    def add_reset_dds(self, timestep):
        pass

    def progRepresentation(self, parse = True):
        if parse:
#            number_ttl_switches = len(self.switchingTimes)
#            if number_ttl_switches >= self.MAX_SWITCHES: raise Exception("Exceeded maximum number of switches {}".format(number_ttl_switches))
            #MR: need to compare MAX DDS SWTICHES HERE.
            self.ddsSettings = self.parse_dds()
            print self.ddsSettings
#            self.ttlProgram = self.parseTTL()
#        return self.ddsSettings, self.ttlProgram
    
    def add_to_dds_program(self, prog, state):
        for name,num in state.iteritems():
            buf = self.parent._intToBuf_coherent(num)
            prog[name] += buf
            
#        self.switchingTimes = {0:numpy.zeros(self.channelTotal, dtype = numpy.int8)} 
#        self.advanceDDS = hardwareConfiguration.channelDict['AdvanceDDS'].channelnumber
#        self.resetDDS = hardwareConfiguration.channelDict['ResetDDS'].channelnumber
    
    def addPulse(self, channel, start, duration):
        """adding TTL pulse, times are in seconds"""
        start = self.secToStep(start)
        duration = self.secToStep(duration)
        self._addNewSwitch(start, channel, 1)
        self._addNewSwitch(start + duration, channel, -1)
    
    def extendSequenceLength(self, timeLength):
        """Allows to extend the total length of the sequence"""
        timeLength = self.secToStep(timeLength)
        self._addNewSwitch(timeLength,0,0)

    def numToHex(self, number):
        '''converts the number to the hex representation for a total of 32 bits
        i.e: 3 -> 00000000...000100 ->  \x00\x00\x03\x00, note that the order of 8bit pieces is switched'''
        a,b = number // 65536, number % 65536
        return str(np.uint16([a,b]).data)

    def _addNewSwitch(self, timeStep, chan, value):
        if self.switchingTimes.has_key(timeStep):
            if self.switchingTimes[timeStep][chan]: raise Exception ('Double switch at time {} for channel {}'.format(timeStep, chan))
            self.switchingTimes[timeStep][chan] = value
        else:
            self.switchingTimes[timeStep] = np.zeros(self.channelTotal, dtype = np.int8)
            self.switchingTimes[timeStep][chan] = value
    
    def parseTTL(self):
        """Returns the representation of the sequence for programming the FPGA"""
        rep = ''
        lastChannels = np.zeros(self.channelTotal)
        powerArray = 2**np.arange(self.channelTotal, dtype = np.uint64)
        for key,newChannels in sorted(self.switchingTimes.iteritems()):
            channels = lastChannels + newChannels #computes the action of switching on the state
            if (channels < 0).any(): raise Exception ('Trying to switch off channel that is not already on')
            channelInt = np.dot(channels,powerArray)
            rep = rep + self.numToHex(key) + self.numToHex(channelInt) #converts the new state to hex and adds it to the sequence
            lastChannels = channels
        rep = rep + 2*self.numToHex(0) #adding termination
        return rep