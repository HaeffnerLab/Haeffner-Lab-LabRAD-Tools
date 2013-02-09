from labrad.units import WithUnit

class pulse_sequence(object):
	
	'''
	Base class for all Pulse Sequences
	Version 1.0
	'''
	
	def __init__(self, start = WithUnit(0, 's'), **kwargs):
		self.start = start
		self.end = start
		self.dds_pulses = []
		self.ttl_pulses = []
		self.replace = kwargs
		self.set_params(self.required_parameters() , **kwargs)
		self.sequence()
	
	@classmethod
	def required_parameters(cls):
		'''
		implemented by the subclass
		
		returns a list of parameters required to executve the pulse sequence
		'''	
		return []
	
	@classmethod
	def required_subsequences(cls):
		'''
		implemente by the subclass
		
		returns a list of of required subsequences
		'''
		return []
	
	@classmethod
	def all_variables(cls):
		'''
		returns a list of all required variables for the current sequence and all used subsequences
		'''
		all_vars = set(cls.required_parameters())
		for subsequence in cls.required_subsequences():
			all_vars = all_vars.union(set(subsequence.required_parameters()))
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
	
	def addSequence(self, sequence, position = None, **kwargs):
		'''insert a subsequence, position is either time or None to insert at the end'''
		#position where sequence is inserted
		if sequence not in self.required_subsequences(): raise Exception ("Adding subsequence {0} that is not listed in the required subequences".format(sequence.__class__.__name__))
		if type(position) == dict: raise Exception ("Don't forget ** in front of replacement dictionary")
		if position is None:
			position = self.end
		#replacement conists of global replacement and key work arguments
		replacement = {}
		replacement.update(self.replace)
		replacement.update(kwargs)
		seq = sequence(start = position, **replacement)
		self.dds_pulses.extend( seq.dds_pulses )
		self.ttl_pulses.extend( seq.ttl_pulses )
		self.end = max(self.end, seq.end)
	
	def programSequence(self, pulser):
		pulser.new_sequence()
		pulser.add_ttl_pulses(self.ttl_pulses)
		pulser.add_dds_pulses(self.dds_pulses)
		pulser.program_sequence()