from dataProcess import dataProcess

class timeResolvedFullFFT(dataProcess):
    """
    Performs and plots the FFT of Time Resolved Photons.
    """
    name = 'timeResolvedFullFFT'
    serversRequired = ['data_vault','timeresolvedfpga','pauls box']
    serversOptional = None
    conflictingProcesses = None
    inputsRequired = ['Measurement Time']
    inputsOptional = [
                      ('Data Vault Directory',"['','TimeResolvedCounts']"),
                      ('Iterations','1'),
                      ('runForever','False')
                      ]
    
    def execute(self):
        print 'running'
        import time
        import numpy
        #import matplotlib
        #matplotlib.use('Qt4Agg')
        #from matplotlib import pyplot
        yield self.do()
       
    def do(self):
        print 'communicating'
        t = self.cxn.timeresolvedfpga
        yield t.set_time_length(0.010)
        yield t.perform_time_resolved_measurement()
        res = yield t.get_result_of_measurement()
        bytelength = res[0][0]
        timelength = res[0][1]
        arr = res[1].asarray
        positions = arr[0];
        elems = arr[1];

    #this process is much faster but equilvant to bitarray.fromstring(raw)
    #arr = numpy.array(b)

        result = numpy.zeros(( bytelength, 8), dtype = numpy.uint8)

        #goes from 255 to [1,1,1,1,1,1,1,1]
        def converter(x):
            str = bin(x)[2:].zfill(8)
            l = [int(s) for s in str]
            return l

        elems = map(converter , elems);
        result[positions] = elems
        result = result.flatten()
        fft = numpy.fft.rfft(result) #returns nice form, faster than fft for real inputs
        timestep = 5*10**-9 #nanoseconds, ADD this to server
        freqs = numpy.fft.fftfreq(result.size, d = timestep)
        freqs = numpy.abs(freqs[0:result.size/2 + 1])
        ampl = numpy.abs(fft)
        print 'done'
        #pyplot.plot(freqs, ampl)
        #pyplot.show()

#    @inlineCallbacks
#    def yieldsomething(self):
#        servers = yield self.cxn.manager.servers()
#        print servers
#        