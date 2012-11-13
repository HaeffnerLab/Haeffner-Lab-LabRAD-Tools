import reloader
reloader.enable(blacklist = ['zope.interface', 'numpy','twisted','labrad'])
#import scripts.PulseSequences.subsequences.OpticalPumpingContinuous
#m = scripts.PulseSequences.subsequences.OpticalPumpingContinuous
import scripts.PulseSequences.delete_later
m = scripts.PulseSequences.delete_later

reloader.reload(m)

#print reloader.get_dependencies(scripts.PulseSequences.subsequences.OpticalPumpingContinuous)