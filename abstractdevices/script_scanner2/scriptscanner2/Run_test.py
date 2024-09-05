import numpy as np
from treedict import TreeDict
import labrad
from labrad.units import WithUnit as U
#from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, DeferredList, returnValue, Deferred
from twisted.internet.threads import blockingCallFromThread
import dvParameters
from analysis import readouts
import sys


def plot_current_sequence(cxn):
    from common.okfpgaservers.pulser.pulse_sequences.plot_sequence import SequencePlotter
    dds = cxn.pulser.human_readable_dds()
    ttl = cxn.pulser.human_readable_ttl()
    channels = cxn.pulser.get_channels()
    sp = SequencePlotter(ttl, dds, channels)
    sp.makePDF()


if __name__=='__main__':
    from common.devel.bum.sequences.pulse_sequence import pulse_sequence
    from lattice.PulseSequences2.RabiFlopping import RabiFlopping
    
    print " I am alive"
    cxn = labrad.connect()
    #pv= cxn.parametervault
    pulser = cxn.pulser
    pv = TreeDict.fromdict({})
    seq = RabiFlopping(pv)
    seq.programSequence(pulser)
    print "programmed pulser"
    
    plot_current_sequence(cxn)
    pulser.start_number(5000)
    print "started 10000 sequences"
    pulser.wait_sequence_done()
    print "done"
    pulser.stop_sequence()
       
 