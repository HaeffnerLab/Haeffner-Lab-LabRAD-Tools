# This keithley_helper file contains some helper functions while running keithley DMM.
# First class is about voltage conversion, so it will covert the voltage into temperature
# Second class is resistance conversion, so it will convert the resistance into temperature

from math import *

class voltage_conversion(object):
    #This class contains helper functions to convert input voltages into associated temperature in Kelvin
    def conversion(self,voltage):
        #This is a conversion function: Convert voltage into Temperature in Kelvin
        # Coeffitients vary depends on different temperature
        #voltage from 1.333V-1.627V
        c1=[7.598874,-6.054714,0.188061,-0.358298,-0.078494,-0.026471,-0.013432,- 0.011013,-0.009895,-0.008241,-0.012511]
        #voltage from 1.119V-1.333V
        c2=[17.226146, -7.739268, 0.468757, -0.019485, 0.208824, -0.270772, 0.219053, -0.120131, 0.096625, -0.024932, 0.038220]
        #voltage from 1.008-1.119
        c3=[59.999998, -39.950840, 1.095917, 1.587186, 0.859736, 0.335571, 0.056868, -0.053521,-0.046177,-0.041731,-0.006274,-0.017138]
        #voltage from 0.5005V-1.008V
        c4=[207.377734,-126.105520,-3.932388,-0.897132,-0.243932,-0.080220, -0.017812,-0.002312,0.001002,0.001299]

        if( 1.333 <= voltage <= 1.627):
            ZL = 1.292788078
            ZU = 1.628987089
            TempK = self.calculation(c1, ZU, ZL, voltage)
            return TempK
        elif (1.119 <= voltage <= 1.333):
            ZL = 1.114338319
            ZU = 1.380313646
            TempK = self.calculation(c2, ZU, ZL, voltage)
            return TempK
        elif (1.008 <= voltage <= 1.119):
            ZL = 0.9863642945
            ZU = 1.12802078
            TempK = self.calculation(c3, ZU, ZL, voltage)
            return TempK
        elif (0.5005 <= voltage <= 1.008):
            ZL = 0.4881727745
            ZU = 1.029436865
            TempK = self.calculation(c4, ZU, ZL, voltage)
            return TempK
        else:
            return 0
        
    def calculation(self,coefficient,ZU,ZL,Z):
        TempK=0
        i = 0
        X = ((Z-ZL)-(ZU-Z))/(ZU-ZL)
        for num in coefficient:
            TempK += (num)*((cos((i*(acos(X))))))
            i += 1    
        return TempK
    
class resistance_conversion(object):
    
    def conversion(self, R):
        temp = [0,0]
        Ac = [5.21195, 4.9193]
        Bc = [2.14594,2.50747]
        Cc = [6.74724,5.85443]
        temp[0] = self.calculation(Ac[0], Bc[0], Cc[0], R)
        temp[1] = self.calculation(Ac[1], Bc[1], Cc[1], R)
        return temp
    
    def calculation(self, A,B,C,R):
        return B/(log(R,10)+ C/log(R,10)-A)
