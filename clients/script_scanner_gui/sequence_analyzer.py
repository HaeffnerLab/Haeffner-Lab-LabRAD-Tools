import numpy as np
import matplotlib.pyplot as plt


"""
This file defines a class called sequence_analyzer, whose purpose is to take raw information from the pulser server,
(namely, the information that sequence_analyzer gets initialized with: human_readable_ttl, human_readable_dds, and channels)
process it, and create a plot of it.

The dds_box class is essentially a wrapper for a matplotlib.collections.PolyCollection object, which is created when plotting
the pulse sequence when fill_between is called to produce the colored boxes which represent the frequency of a pulse.
"""




###########################################
# Functions to be used by the classes below
###########################################

def squarify(x, y):
    """Take a set of x, y coordinates and return a new set of x, y coordinates, which, if plotted,
    produce a plot with flat boxes """
    assert len(x)==len(y)
    x_sq = [x[0]]
    y_sq = [y[0]]
    last_y = y[0]
    for (a, b) in zip(x[1:], y[1:]):
        if b != last_y:
            x_sq.extend((a, a))
            y_sq.extend((last_y, b))
            last_y = b
    x_sq.append(x[-1])
    y_sq.append(y[-1])
    return (np.array(x_sq), np.array(y_sq))

def different_from_last(array, first_true=True):
    """Takes a list and checks element-by element whether the element is different from the one before it"""
    return [first_true] + [array[i] != array[i-1] for i in range(1, len(array))]

def find3digits(string):
    """Returns the first substring of 3 consecutive digits, if it exists
    Used for checking which laser a channel is likely to be assigned to (e.g. 729, 866, etc.)"""
    for (i, char) in enumerate(string[:-2]):
        if char.isdigit():
            if string[i+1].isdigit() and string[i+2].isdigit():
                return string[i:i+3]
    return None

def is_same_laser(channel1, channel2):
    """Determines whether 2 channels are assigned to the same laser, as defined by find3digits()"""
    if find3digits(channel1):
        return find3digits(channel1) == find3digits(channel2)




class dds_box():
    """This is a helper class that wraps information about a box which gets plotted by the pulse sequence visualizer.
    This information is used by the pulse sequence analyzer for the event of a mouse hover over one of the boxes, in which case
    the methods of this class are called in order to retreive information about the pulse which is being hovered over, 
    so that that information may be displayed on the plot for the user."""
    def __init__(self, box, sequence, channel, i_start, i_end, offset, scale):
        self.box = box
        self.sequence = sequence
        self.channel = channel
        self.i_start = i_start
        self.i_end = i_end
        self.offset = offset
        self.scale = scale

    def frequency(self):
        return self.sequence.get_dds_freqs_ampls(self.channel)[0][self.i_start]

    def amplitude(self):
        return self.sequence.get_dds_freqs_ampls(self.channel)[1][self.i_start]

    def starttime(self):
        return self.sequence.dds_dict['times'][self.i_start]

    def duration(self):
        return self.sequence.dds_dict['times'][self.i_end] - self.starttime()




class sequence_analyzer():
    """
    This class stores all information, raw and processed, about a pulse sequence.
    Initialization is intended to be done using data grabbed from a LabRAD client who calls the following methods of the pulser LadRAD server:
    human_readable_dds, human_readable_ttl, and get_channels.

    The processed pulse sequence information is stored in two dictionaries, one for DDS pulses ("dds_dict") and one for TTL pulses ("ttl_dict").
    See _make_ttl_dict and _make_dds_dict for information about how these dictionaries are organized.

    The main method of this class is create_full_plot, which creates a matplotlib visualization of the pulse sequence on a matplotlib.axes.Axes
    class which is passed into the method. The rest of the methods used by this one for the purpose of making the plot.

    """
    def __init__(self, human_readable_ttl, human_readable_dds, channels):
        self.raw_ttl = human_readable_ttl
        print self.raw_ttl
        print len(self.raw_ttl[0][1])

        self.raw_dds = human_readable_dds
        self.raw_channels = channels

        self.ttl_dict = self._make_ttl_dict()
        self.dds_dict = self._make_dds_dict()

        self.ttl_channels = [key for key in self.ttl_dict.keys() if key is not 'times']
        self.dds_channels = [key for key in self.dds_dict.keys() if key is not 'times']

        self.dds_boxes = []


    def _make_ttl_dict(self):
        """
        Takes human-readable TTL (retrieved from the pulser's 'human_readable_ttl' function) and converts it into a dictionary.  

        The keys in this dictionary are 'times', which is a list of all times (in seconds) when there is a change to a TTL pulse, plus one key
        for each TTL channel. ttl_dict[channel] is a list of binary states of that TTL channel, one for each time in ttl_dict['times'].
        TTL channels which are unused for the whole pulse sequence are excluded.
        """
        
        ttl_dict = {}

        # Create list of times
        ttl_times = [float(time[0]) for time in self.raw_ttl[:-1]]
        ttl_dict['times'] = ttl_times

        # Create list of channels, ordered by the channel number
        channel_list = [None]*32
        print self.raw_channels
        print 'channel_list length:', len(channel_list)
        for channel in self.raw_channels:
            print channel[1]
            channel_list[channel[1]] = channel[0]
        print channel_list

        # Organize the raw info in raw_ttl into the dictionary ttl_dict
        ttl_array_full = np.array([[int(channel_setting) for channel_setting in time[1]] for time in self.raw_ttl[:-1]])
        for (i, channel) in enumerate(channel_list):
            # Exclude unused channels
            if np.any(ttl_array_full[:, i]):
                ttl_dict[channel] = ttl_array_full[:, i]

        print ttl_dict
        return ttl_dict


    def _make_dds_dict(self):
        """
        Takes human-readable DDS (retrieved from the pulser's 'human_readable_dds' function) and converts it into a dictionary.  

        The keys in this dictionary are 'times', which is a list of all times (in seconds) when there is a change to a DDS pulse, plus one key
        for each DDS channel.
        dds_dict[channel] is a list of two lists:
        dds_channel[0] is a list of the frequencies of that DDS channel (in MHz), one for each time in dds_dict['times'].
        dds_channel[1] is a list of the amplitudes of that DDS channel (in dBm), one for each time in dds_dict['times'].
        
        DDS channels which are never turned on for the whole pulse sequence are excluded.
        """

        dds_dict = {}

        # Create list of times when the DDS is advanced (which is a subset of the TTL times)
        if not('AdvanceDDS' in self.ttl_dict):
            raise Exception("No DDS-advancing pulses present in pulse sequence.")
        dds_times = [self.ttl_dict['times'][0]] + [self.ttl_dict['times'][i] for i in range(len(self.ttl_dict['times'])) if self.ttl_dict['AdvanceDDS'][i]]
        if 'ResetDDS' in self.ttl_dict:
            dds_times.extend([self.ttl_dict['times'][i] for i in range(len(self.ttl_dict['times'])) if self.ttl_dict['ResetDDS'][i]])
        dds_dict['times'] = dds_times

        # Organize the raw info in raw_dds into the dictionary dds_dict
        for setting in self.raw_dds:
            channel_name = setting[0]
            if not channel_name in dds_dict:
                dds_dict[channel_name] = [[], []]
            dds_dict[channel_name][0].extend([setting[1]])
            dds_dict[channel_name][1].extend([setting[2]])
        for channel_name in dds_dict.keys():
            if channel_name is not 'times':
                #Exclude unused channels
                if not np.any(dds_dict[channel_name][0]) or len(set(dds_dict[channel_name][1]))<=1:
                    del dds_dict[channel_name]
                else:
                    dds_dict[channel_name][0].extend([dds_dict[channel_name][0][-1]])
                    dds_dict[channel_name][1].extend([dds_dict[channel_name][1][-1]])
                    assert len(dds_dict[channel_name][0]) == len(dds_dict['times']), 'Number of frequencies for channel {} does not match number of times.'.format(channel_name)
                    assert len(dds_dict[channel_name][1]) == len(dds_dict['times']), 'Number of amplitudes for channel {} does not match number of times.'.format(channel_name)

        return dds_dict


    def create_ttl_plot(self, channel, axes, offset, scale=1.0):
        """Makes a plot of TTL state vs. time for a given channel, on a given set of matplotlib axes, with some offset and scale."""
        times = self.ttl_dict['times']
        ttl = self.ttl_dict[channel]
        (times_sqr, ttl_sqr) = squarify(times, ttl)
        axes.plot(1e3*times_sqr, offset+scale*ttl_sqr, color='k', linewidth=0.75, label=channel)
        axes.annotate(channel, xy=(0, offset-0.1*scale), horizontalalignment='left', verticalalignment='top', weight='bold')


    def create_dds_plot(self, channel, axes, offset, scale=1.0):
        """Makes a plot of DDS state vs. time for a given channel, on a given set of matplotlib axes, with some offset and scale.
        Height corresponds to amplitude, and color of the fill_between corresponds to frequency.
        For each DDS pulse in this channel, a dds_box class instance is also created. This is added to the present sequence_analyzer's list of all dds_box objects, self.dds_boxes, for later use by the pulse sequence visualizer."""
        times = self.dds_dict['times']

        # Create a list of all other DDS channels which correspond to the same laser.
        same_laser = []
        for other_channel in self.dds_channels:
            if other_channel is not channel:
                if is_same_laser(channel, other_channel):
                    same_laser.append(other_channel)

        # Create a "squarified" plot of the DDS amplitude as a function of time, normalized to the largest amplitude present for this channel.
        (freqs_normlzd, amps_normlzd) = self.normalized_freqsandamps(channel, other_channels=same_laser)
        (times_sqr, amps_sqr) = squarify(times, amps_normlzd)
        linecolor='k'
        axes.plot(1e3*times_sqr, offset+amps_sqr, color=linecolor, linewidth=0.75, label=channel)
        axes.annotate(channel, xy=(0, offset-0.1*scale), horizontalalignment='left', verticalalignment='top', weight='bold')

        # Get a list of all indices of the list dds_dict['times'] in which either the frequency or amplitude of this DDS channel is changed.
        # This information will be used to create the "boxes" which are the colored rectangles on the plot representing a pulse; there will be one box for each change in frequency or amplitude (IF the amplitude is not its minimum, i.e. off).
        freq_changes = different_from_last(freqs_normlzd)
        amp_changes = different_from_last(amps_normlzd)
        either_changes = np.logical_or(freq_changes, amp_changes)
        change_indices = [i for i in range(len(either_changes[:-1])) if either_changes[i]]
        
        # Add a fill_between object to the axes for every pulse, and also create a dds_box object to store in the present sequence_analyzer object.
        cmap = plt.get_cmap('jet_r')
        for i_ch in range(len(change_indices)-1):
            i_curr = change_indices[i_ch]
            i_next = change_indices[i_ch+1]
            if amps_normlzd[i_curr]:
                box = axes.fill_between([1e3*times[i_curr], 1e3*times[i_next]], [offset, offset], [offset+scale*amps_normlzd[i_curr], offset+scale*amps_normlzd[i_curr]], facecolor=cmap(freqs_normlzd[i_curr]))
                self.dds_boxes.append(dds_box(box, self, channel, i_curr, i_next, offset, scale))


    def get_dds_freqs_ampls(self, channel):
        # Returns frequencies and amplitudes of the specified DDS channel, for all times
        return (self.dds_dict[channel][0], self.dds_dict[channel][1])


    def when_on(self, channel):
        # Returns a list of indices when a specified DDS channel is on (at any amplitude other than the minimum)
        (_, ampl_array) = self.get_dds_freqs_ampls(channel)
        min_ampl = min(ampl_array)
        return [ampl!=min_ampl for ampl in ampl_array]


    def get_freqs_while_on(self, channel):
        # Returns a list of all frequencies that the specified DDS channel is set to, excluding those when it is off.
        is_on = self.when_on(channel)
        (freq_array, _) = self.get_dds_freqs_ampls(channel)
        return [freq_array[i] for i in range(len(freq_array)) if is_on[i]]


    def normalized_freqsandamps(self, channel, other_channels=[]):
        # Returns a tuple of two lists: normalized frequencies, and normalized amplitudes.
        # Frequencies are normalized between 0 and 1, with 0 being the lowest frequency experienced COLLECTIVELY by the specified channel PLUS any channels specified by other_channels, and 1 being the highest.
        # Amplitudes are also normalized between 0 and 1, with 0 being the lowest amplitude experienced by the specified channel only, and 1 being the highest.
        (freq_array, ampl_array) = self.get_dds_freqs_ampls(channel)

        # Check to make sure this channels is actually turned on during this pulse sequence
        if max(ampl_array) == min(ampl_array):
            raise Exception('Channel {} does not change amplitude and should not have been plotted'.format(channel))
        amps_normlzd = (np.array(ampl_array) - min(ampl_array))/(max(ampl_array)-min(ampl_array))
        
        # Get list of frequencies for nonzero pulse amplitudes
        freqs_while_on = self.get_freqs_while_on(channel)
        for other_channel in other_channels:
            freqs_while_on.extend(self.get_freqs_while_on(other_channel))
        
        # Normalize the frequencies (and simply set all to zero if the frequency never changes)
        if min(freqs_while_on) == max(freqs_while_on):
            freqs_normlzd = np.zeros_like(freq_array, dtype='float')
        else:
            freqs_normlzd = (np.array(freq_array) - min(freqs_while_on))/(max(freqs_while_on)-min(freqs_while_on))
        return (freqs_normlzd, amps_normlzd)


    def create_full_plot(self, axes):
        # Creates a TTL plot and a DDS plot for every TTL/DDS channel, progressively offsetting them on the axes
        offset = 0
        for channel in self.ttl_channels:
            self.create_ttl_plot(channel, axes, offset, scale=0.5)
            offset += 0.75
        offset += 0.5
        offset = np.ceil(offset)
        for channel in self.dds_channels:
            self.create_dds_plot(channel, axes, offset)
            offset += 1.5