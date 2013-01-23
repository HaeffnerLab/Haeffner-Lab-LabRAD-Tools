def valToInt(channel, freq, ampl, phase=0):
	ans = 0
    for val,r,m, precision in [(freq,channel.boardfreqrange, 1, 32), (ampl,channel.boardamplrange, 2 ** 32,  16), (phase,channel.boardphaserange, 2 ** 48,  16)]:
    	minim, maxim = r
        resolution = (maxim - minim) / float(2**precision - 1)
       	seq = int((val - minim)/resolution) #sequential representation
        ans += m*seq
    return ans

def _intToBuf(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''
        #converts value to buffer string, i.e 128 -> \x00\x00\x00\x80
	a, b = num // 256**2, num % 256**2
	arr = array.array('B', [a % 256 ,a // 256, b % 256, b // 256])
	ans = arr.tostring()
	print arr
	return ans

