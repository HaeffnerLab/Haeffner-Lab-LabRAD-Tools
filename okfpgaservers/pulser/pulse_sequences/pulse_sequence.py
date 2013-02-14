from pulse_sequences_config import dds_name_dictionary as dds_config
from labrad.units import WithUnit

class pulse_sequence(object):
	
	'''
	Base class for all Pulse Sequences
	Version 1.0
	'''
	
	required_parameters = []
	required_subsequences = []
	
	def __init__(self, start = WithUnit(0, 's'), **kwargs):
		self.start = start
		self.end = start
		self._dds_pulses = []
		self._ttl_pulses = []
		self.replace = kwargs
		self.set_params(self.required_parameters , **kwargs)
		self.sequence()
	
	@classmethod
	def all_variables(cls):
		'''
		returns a list of all required variables for the current sequence and all used subsequences
		'''
		all_vars = set(cls.required_parameters)
		for subsequence in cls.required_subsequences:
			all_vars = all_vars.union(set(subsequence.required_parameters))
		return list(all_vars)
	
	def sequence(self):
		'''
		implemented by subclass
		'''
	
	def set_params(self, params, **replace):
		for param in params:
			if param in self.__dict__: raise Exception ("Overwrite parameter {0} in the {1} Pulse Sequence".format(param, self.__class__.__name__))
			try:
				self.__dict__[param] = replace[param]
			except KeyError:
				raise Exception('{0} value not provided for the {1} Pulse Sequence'.format(param, self.__class__.__name__))
	
	def addDDS(self, channel, start, duration, frequency, amplitude):
		"""
		add a dds pulse to the pulse sequence
		"""
		dds_channel = dds_config.get(channel, None)
		if dds_channel is not None:
			#additional configuration provided
			channel = dds_channel.name
			frequency = dds_channel.freq_conversion(frequency)
			amplitude = dds_channel.ampl_conversion(amplitude)				
		self._dds_pulses.append((channel, start, duration, frequency, amplitude))
	
	def addTTL(self, channel, start, duration):
		"""
		add a ttl pulse to the pulse sequence
		"""
		self._ttl_pulses.append((channel, start, duration))
	
	def addSequence(self, sequence, position = None, **kwargs):
		'''insert a subsequence, position is either time or None to insert at the end'''
		#position where sequence is inserted
		if sequence not in self.required_subsequences: raise Exception ("Adding subsequence {0} that is not listed in the required subequences".format(sequence.__class__.__name__))
		if type(position) == dict: raise Exception ("Don't forget ** in front of replacement dictionary")
		if position is None:
			position = self.end
		#replacement conists of global replacement and keyword arguments
		replacement = {}
		replacement.update(self.replace)
		replacement.update(kwargs)
		seq = sequence(start = position, **replacement)
		self._dds_pulses.extend( seq._dds_pulses )
		self._ttl_pulses.extend( seq._ttl_pulses )
		self.end = max(self.end, seq.end)
	
	def programSequence(self, pulser):
		pulser.new_sequence()
		pulser.add_ttl_pulses(self._ttl_pulses)
		pulser.add_dds_pulses(self._dds_pulses)
		pulser.program_sequence()