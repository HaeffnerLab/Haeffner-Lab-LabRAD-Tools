from pulse_sequences_config import dds_name_dictionary as dds_config
from labrad.units import WithUnit
from treedict import TreeDict

class pulse_sequence(object):
	
	'''
	Base class for all Pulse Sequences
	Version 2 -- made for new script scanner project
	'''
	
	def __init__(self, parameter_dict, start = WithUnit(0, 's')):
		if not type(parameter_dict) == TreeDict: raise Exception ("replacement_dict must be a TreeDict in sequence {0}".format(self.__class__.__name__))
		self.start = start
		self.end = start
		self._dds_pulses = []
		self._ttl_pulses = []
		self.replace = parameter_dict
		#self.parameters = self.fill_parameters(self.required_parameters , self.replace)
		self.parameters = parameter_dict
		self.sequence()

	def sequence(self):
		'''
		implemented by subclass
		'''
	
	def fill_parameters(self, params, replace):
		if not len(params) == len(set(params)):
			raise Exception ("Duplicate required parameters found in {0}".format(self.__class__.__name__))
		new_dict = TreeDict()
		for collection,parameter_name in params:
			treedict_key = '{0}.{1}'.format(collection,parameter_name)
			try:
				new_dict[treedict_key] = replace[treedict_key]
			except KeyError:
				raise Exception('{0} {1} value not provided for the {2} Pulse Sequence'.format(collection, parameter_name, self.__class__.__name__))
		return new_dict
	
	def addDDS(self, channel, start, duration, frequency, amplitude, phase = WithUnit(0, 'deg'), profile = 0):
		"""
		add a dds pulse to the pulse sequence
		"""
		#print "Profile: ", profile
		dds_channel = dds_config.get(channel, None)
		if dds_channel is not None:
			#additional configuration provided
			channel = dds_channel.name
			frequency = dds_channel.freq_conversion(frequency)
			amplitude = dds_channel.ampl_conversion(amplitude)
			phase = dds_channel.phase_conversion(phase)
		self._dds_pulses.append((channel, start, duration, frequency, amplitude, phase, profile))
	
	def addTTL(self, channel, start, duration):
		"""
		add a ttl pulse to the pulse sequence
		"""
		self._ttl_pulses.append((channel, start, duration))
	
	def addSequence(self, sequence, replacement_dict = TreeDict(), position = None):
		'''insert a subsequence, position is either time or None to insert at the end'''
		#if not type(replacement_dict) == TreeDict: raise Exception ("replacement_dict must be a TreeDict")
		if position is None:
			position = self.end
		#replacement conists of global replacement and keyword arguments
		replacement = TreeDict()
		replacement.update(self.replace)
		replacement.update(replacement_dict)
		seq = sequence(replacement, start = position)
		self._dds_pulses.extend( seq._dds_pulses )
		#print 'heres the seq pulses'
		#print seq._ttl_pulses
		self._ttl_pulses.extend( seq._ttl_pulses )
		self.end = max(self.end, seq.end)
	
	def programSequence(self, pulser):
		pulser.new_sequence()
		#print self._ttl_pulses
		pulser.add_ttl_pulses(self._ttl_pulses)
		pulser.add_dds_pulses(self._dds_pulses)
		pulser.program_sequence()

	def calc_freq(self, carrier='S-1/2D-1/2', sideband=None,order=0):
		'''calculates the frequency of the 729 DP drive from the carriers and sidebands
		in the parameter vault
		'''
		carrier_translation = {'S+1/2D-3/2':'c0',
							   'S-1/2D-5/2':'c1',
							   'S+1/2D-1/2':'c2',
							   'S-1/2D-3/2':'c3',
							   'S+1/2D+1/2':'c4',
							   'S-1/2D-1/2':'c5',
							   'S+1/2D+3/2':'c6',
							   'S-1/2D+1/2':'c7',
							   'S+1/2D+5/2':'c8',
							   'S-1/2D+3/2':'c9',
							   }
		freq=self.parameters.Carriers[carrier_translation[carrier]]
		try: 
			freq=self.parameters.Carriers[carrier_translation[carrier]]
		except:
			raise Exception('carrier not found') 
		if sideband is not None:
			try: 
				freq = freq+ 1.0*self.parameters.TrapFrequencies[sideband]*order
			except:
				raise Exception('sideband not found') 
		return freq
	
	@classmethod
	def execute_external(cls, scan, fun = None):
		'''
		scan  = (scan_param, minim, maxim, seps, unit)
		fun = function to evaluate on the result of the scan 
		'''
		from common.devel.bum.scriptscanner2.sequence_wrapper import pulse_sequence_wrapper
		psw = pulse_sequence_wrapper(cls)
		scan_param, minim, maxim, steps, unit = scan
		psw.set_scan(scan_param, minim, maxim, steps, unit)
		psw.run(0)
