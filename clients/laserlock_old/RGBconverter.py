# -*- coding: utf-8 -*-
#the following wavelength to RGB conversion was written by
#http://codingmess.blogspot.com/2009/05/conversion-of-wavelength-in-nanometers.html
class RGBconverter():
	def wav2RGB(self, wavelength):
		w = wavelength
		if w >= 380 and w < 440:
			R = -(w - 440.) / (440. - 350.)
			G = 0.0
			B = 1.0
		elif w >= 440 and w < 490:
			R = 0.0
			G = (w - 440.) / (490. - 440.)
			B = 1.0
		elif w >= 490 and w < 510:
			R = 0.0
			G = 1.0
			B = -(w - 510.) / (510. - 490.)
		elif w >= 510 and w < 580:
			R = (w - 510.) / (580. - 510.)
			G = 1.0
			B = 0.0
		elif w >= 580 and w < 645:
			R = 1.0
			G = -(w - 645.) / (645. - 580.)
			B = 0.0
		elif w >= 645 and w <= 780:
			R = 1.0
			G = 0.0
			B = 0.0
		elif w > 780:
			R = 1.0
			G = 0.0
			B = 0.0
		elif w < 380:
			R = 1.0
			G = 0.0
			B = 1
		else:
			R = 0.0
			G = 0.0
			B = 0.0
		# intensity correction
		if w >= 380 and w < 420:
			SSS = 0.3 + 0.7*(w - 350) / (420 - 350)
		elif w >= 420 and w <= 700:
			SSS = 1.0
		elif w > 700 and w <= 780:
			SSS = 0.3 + 0.7*(780 - w) / (780 - 700)
		elif w > 780:
			SSS = 0.3
		elif w < 380:
			SSS = 0.6
		else:
			SSS = 0
		SSS *= 255
		return [int(SSS*R), int(SSS*G), int(SSS*B)]