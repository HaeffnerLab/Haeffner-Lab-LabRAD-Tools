class configuration(object):
    '''
    class for configuring the pulser pulse sequences
    '''
    '''
    channel_dictionary provides a translation between the channels of the pulse sequence
    and the pulser dds channel names.  This allows to keep pulse sequences easier to read.
    There can be multiple keys for the same value.
    '''
    channel_name_dictionary = {
                               '110DP':'110DP',
                               'radial':'radial',
                               '854DP':'854DP',
                               '866DP':'866DP',
                               '729DP':'729DP',
                               '397':'110DP',
    }