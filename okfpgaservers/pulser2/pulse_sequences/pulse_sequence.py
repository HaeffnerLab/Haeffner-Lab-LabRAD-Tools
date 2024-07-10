from pulse_sequences_config import dds_name_dictionary as dds_config
from labrad.units import WithUnit
from treedict import TreeDict

class pulse_sequence(object):
	
	'''
	Base class for all Pulse Sequences
	Version 1.1
	'''
	required_parameters = []
	required_subsequences = []
	replaced_parameters = {}
	
	def __init__(self, parameter_dict, start = WithUnit(0, 's')):
		if not type(parameter_dict) == TreeDict: raise Exception ("replacement_dict must be a TreeDict in sequence {0}".format(self.__class__.__name__))
		self.start = start
		self.end = start
		self._dds_pulses = []
		self._ttl_pulses = []
		self.replace = parameter_dict
		self.parameters = self.fill_parameters(self.required_parameters , self.replace)
		self.sequence()
	
	@classmethod
	def all_required_parameters(cls):
		'''
		returns a list of all required variables for the current sequence and all used subsequences
		'''
		required = set(cls.required_parameters)
		for subsequence in cls.required_subsequences:
			replaced = set(cls.replaced_parameters.get(subsequence, []))
			additional = set(subsequence.all_required_parameters())
			additional.difference_update(replaced)
			required = required.union(additional)
		required = list(required)
		return required
	
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
	
	def addDDS(self, channel, start, duration, frequency, amplitude, phase = WithUnit(0, 'deg'), ramp_rate = WithUnit(0,'MHz'), amp_ramp_rate = WithUnit(0,'dB')):
		"""
		add a dds pulse to the pulse sequence
		"""
		dds_channel = dds_config.get(channel, None)
		if dds_channel is not None:
			#additional configuration provided
			channel = dds_channel.name
			frequency = dds_channel.freq_conversion(frequency)
			amplitude = dds_channel.ampl_conversion(amplitude)
			phase = dds_channel.phase_conversion(phase)
			ramp_rate = dds_channel.ramprate_conversion(ramp_rate)
			amp_ramp_rate = dds_channel.amp_ramp_rate_conversion(amp_ramp_rate)
		self._dds_pulses.append((channel, start, duration, frequency, amplitude, phase, ramp_rate, amp_ramp_rate))
	
	def addTTL(self, channel, start, duration):
		"""
		add a ttl pulse to the pulse sequence
		"""
		self._ttl_pulses.append((channel, start, duration))
	
	def addSequence(self, sequence, replacement_dict = TreeDict(), position = None):
		'''insert a subsequence, position is either time or None to insert at the end'''
		if sequence not in self.required_subsequences: raise Exception ("Adding subsequence {0} that is not listed in the required subequences".format(sequence.__class__.__name__))
		if not type(replacement_dict) == TreeDict: raise Exception ("replacement_dict must be a TreeDict")
		for replacement_key in replacement_dict.keys():
			parsed = tuple(replacement_key.split('.'))
			key_list = self.replaced_parameters.get(sequence, [])
			if not parsed in key_list:
				raise Exception("Error in {0}: replacing the key {1} in the sequence {2} that is not listed among the replacement parameters".format(self, replacement_key, sequence))
		if position is None:
			position = self.end
		#replacement conists of global replacement and keyword arguments
		replacement = TreeDict()
		replacement.update(self.replace)
		replacement.update(replacement_dict)
		seq = sequence(replacement, start = position)
		self._dds_pulses.extend( seq._dds_pulses )
		self._ttl_pulses.extend( seq._ttl_pulses )
		self.end = max(self.end, seq.end)
	
	def programSequence(self, pulser):
		pulser.new_sequence()
		pulser.add_ttl_pulses(self._ttl_pulses)
		pulser.add_dds_pulses(self._dds_pulses)
		pulser.program_sequence()