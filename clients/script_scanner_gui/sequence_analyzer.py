import numpy as np
import matplotlib.pyplot as plt



def squarify(x, y):
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

def different_from_last(array):
    return [True] + [array[i] != array[i-1] for i in range(1, len(array))]

def find3digits(string):
    for (i, char) in enumerate(string[:-2]):
        if char.isdigit():
            if string[i+1].isdigit() and string[i+2].isdigit():
                return string[i:i+3]
    return None

def is_same_laser(channel1, channel2):
    return find3digits(channel1) == find3digits(channel2)




class sequence_analyzer():
    def __init__(self, human_readable_ttl, human_readable_dds, channels):
        self.raw_ttl = human_readable_ttl
        self.raw_dds = human_readable_dds
        self.raw_channels = channels

        self.ttl_dict = self._make_ttl_dict()
        self.dds_dict = self._make_dds_dict()

        self.ttl_channels = [key for key in self.ttl_dict.keys() if key is not 'times']
        self.dds_channels = [key for key in self.dds_dict.keys() if key is not 'times']

    def _make_ttl_dict(self):
        """Takes human-readable ttl (retrieved from the pulser's 'human_readable_ttl' function) and converts it into a dictionary of  """
        
        ttl_dict = {}

        # Create list of times
        ttl_times = [float(time[0]) for time in self.raw_ttl[:-1]]
        ttl_dict['times'] = ttl_times

        # Create list of channels, ordered by the channel number
        channel_list = [None]*len(self.raw_channels)
        for channel in self.raw_channels:
            channel_list[channel[1]] = channel[0]

        # 
        ttl_array_full = np.array([[int(channel_set) for channel_set in time[1]] for time in self.raw_ttl[:-1]])
        for (i, channel) in enumerate(channel_list):
            if np.any(ttl_array_full[:, i]):
                ttl_dict[channel] = ttl_array_full[:, i]

        return ttl_dict


    def _make_dds_dict(self):
        """"""

        dds_dict = {}

        # Create list of times when the DDS is advanced (which is a subset of the TTL times)
        if not('AdvanceDDS' in self.ttl_dict):
            raise Exception("No DDS-advancing pulses present in pulse sequence.")
        dds_times = [self.ttl_dict['times'][0]] + [self.ttl_dict['times'][i] for i in range(len(self.ttl_dict['times'])) if self.ttl_dict['AdvanceDDS'][i]]
        if 'ResetDDS' in self.ttl_dict:
            dds_times.extend([self.ttl_dict['times'][i] for i in range(len(self.ttl_dict['times'])) if self.ttl_dict['ResetDDS'][i]])
        dds_dict['times'] = dds_times

        # 
        for setting in self.raw_dds:
            channel_name = setting[0]
            if not channel_name in dds_dict:
                dds_dict[channel_name] = [[], []]
            dds_dict[channel_name][0].extend([setting[1]])
            dds_dict[channel_name][1].extend([setting[2]])
        for channel_name in dds_dict.keys():
            if channel_name is not 'times':
                if not np.any(dds_dict[channel_name][0]) or len(set(dds_dict[channel_name][1]))<=1:
                    del dds_dict[channel_name]
                else:
                    dds_dict[channel_name][0].extend([dds_dict[channel_name][0][-1]])
                    dds_dict[channel_name][1].extend([dds_dict[channel_name][1][-1]])
                    assert len(dds_dict[channel_name][0]) == len(dds_dict['times']), 'Number of frequencies for channel {} does not match number of times.'.format(channel_name)
                    assert len(dds_dict[channel_name][1]) == len(dds_dict['times']), 'Number of amplitudes for channel {} does not match number of times.'.format(channel_name)

        return dds_dict


    def create_ttl_plot(self, channel, axis, offset, scale=1.0):
        times = self.ttl_dict['times']
        ttl = self.ttl_dict[channel]
        (times_sqr, ttl_sqr) = squarify(times, ttl)
        axis.plot(1e3*times_sqr, offset+scale*ttl_sqr, color='k', linewidth=0.5)
        axis.annotate(channel, xy=(0, offset + 0.5*scale), horizontalalignment='right')


    def get_dds_freqs_ampls(self, channel):
        return (self.dds_dict[channel][0], self.dds_dict[channel][1])


    def get_freqs_while_on(self, channel):
        (freq_array, ampl_array) = self.get_dds_freqs_ampls(channel)
        min_ampl = min(ampl_array)
        return [freq_array[i] for i in range(len(freq_array)) if ampl_array[i]!=min_ampl]


    def normalized_freqsandamps(self, channel, other_channels=[]):
        (freq_array, ampl_array) = self.get_dds_freqs_ampls(channel)

        if max(ampl_array) == min(ampl_array):
            raise Exception('Channel {} does not change amplitude and should not have been plotted'.format(channel))
        amps_normlzd = (np.array(ampl_array) - min(ampl_array))/(max(ampl_array)-min(ampl_array))
        
        freqs_while_on = self.get_freqs_while_on(channel)
        for other_channel in other_channels:
            freqs_while_on.extend(self.get_freqs_while_on(other_channel))
        
        if min(freqs_while_on) == max(freqs_while_on):
            freqs_normlzd = np.zeros_like(freq_array, dtype='float')
        else:
            freqs_normlzd = (np.array(freq_array) - min(freqs_while_on))/(max(freqs_while_on)-min(freqs_while_on))
        return (freqs_normlzd, amps_normlzd)


    def create_dds_plot(self, channel, axis, offset, scale=1.0):
        times = self.dds_dict['times']

        same_laser = []
        for other_channel in self.dds_channels:
            if other_channel is not channel:
                if is_same_laser(channel, other_channel):
                    same_laser.append(other_channel)

        (freqs_normlzd, amps_normlzd) = self.normalized_freqsandamps(channel, other_channels=same_laser)
        (times_sqr, amps_sqr) = squarify(times, amps_normlzd)
        linecolor='k'
        axis.plot(1e3*times_sqr, offset+amps_sqr, color=linecolor, linewidth=0.5)
        axis.annotate(channel, xy=(0, offset + 0.5*scale), horizontalalignment='right')

        freq_changes = different_from_last(freqs_normlzd)
        amp_changes = different_from_last(amps_normlzd)
        either_changes = np.logical_or(freq_changes, amp_changes)
        change_indices = [i for i in range(len(either_changes[:-1])) if either_changes[i]]
        
        cmap = plt.get_cmap('jet_r')
        for i_ch in range(len(change_indices)-1):
            i_curr = change_indices[i_ch]
            i_next = change_indices[i_ch+1]
            if amps_normlzd[i_curr]:
                axis.fill_between([1e3*times[i_curr], 1e3*times[i_next]], [offset, offset], [offset+scale*amps_normlzd[i_curr], offset+scale*amps_normlzd[i_curr]], facecolor=cmap(freqs_normlzd[i_curr]))


    def create_full_plot(self, axis):
        offset = 0
        for channel in self.ttl_channels:
            self.create_ttl_plot(channel, axis, offset, scale=0.5)
            offset += 0.75
        offset += 0.5
        offset = np.ceil(offset)
        for channel in self.dds_channels:
            self.create_dds_plot(channel, axis, offset)
            offset += 1.5