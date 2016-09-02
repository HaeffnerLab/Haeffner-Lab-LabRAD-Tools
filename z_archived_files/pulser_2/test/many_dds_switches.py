import labrad

channel = '866DP'
repeats = 2000

with labrad.connect() as cxn:
    p = cxn.pulser
    for i in range(repeats):
        p.output(channel, False)
        p.output(channel, True)