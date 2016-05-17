import math
import matplotlib.pyplot as plt


class voltage_conversion(object):
    #This class contains helper functions to convert input voltages into associated temperature in Kelvin
    
#    def plot(self,x,y):
#        plt.plot(x,y,color="k",marker="*",markersize=6)
#        plt.xlabel('Temperature (K)') # x-axis
#        plt.ylabel('Voltage (V)') # y-axis
#        plt.show()
    
    def conversion(self,voltage):
        #This is a conversion function: Convert voltage into Temperature in Kelvin
        
        #coeffecients
        #voltage from 1.333V-1.627V
        coefficient1=[7.598874,-6.054714,0.188061,-0.358298,-0.078494,-0.026471,-0.013432,- 0.011013,-0.009895,-0.008241,-0.012511]
        #voltage from 1.119V-1.333V
        coefficient2=[17.226146, -7.739268, 0.468757, -0.019485, 0.208824, -0.270772, 0.219053, -0.120131, 0.096625, -0.024932, 0.038220]
        #voltage from 1.008-1.119
        coefficient3=[59.999998, -39.950840, 1.095917, 1.587186, 0.859736, 0.335571, 0.056868, -0.053521,-0.046177,-0.041731,-0.006274,-0.017138]
        #voltage from 0.5005V-1.008V
        coefficient4=[207.377734,-126.105520,-3.932388,-0.897132,-0.243932,-0.080220, -0.017812,-0.002312,0.001002,0.001299]
        
        if( 1.333 <= voltage <= 1.627):
            ZL = 1.292788078
            ZU = 1.628987089
            f1=self.calculation(coefficient1,ZU,ZL,voltage)
            return f1
        
        elif (1.119 <= voltage <= 1.333):
            ZL = 1.114338319
            ZU = 1.380313646
            f2=self.calculation(coefficient2,ZU,ZL,voltage)
            return f2
        
        elif (1.008 <= voltage <= 1.119):
            ZL = 0.9863642945
            ZU = 1.12802078
            f3=self.calculation(coefficient3,ZU,ZL,voltage)
            return f3
        
        elif (0.5005 <= voltage <= 1.008):
            ZL = 0.4881727745
            ZU = 1.029436865
            f4=self.calculation(coefficient4,ZU,ZL,voltage)
            return f4
        else:
            return 0
    
    def calculation(self,coefficient,ZU,ZL,Z):
        TempK=0
        count=0
        X = ((Z-ZL)-(ZU-Z))/(ZU-ZL)
        for num in coefficient:
            TempK+= (num)*((math.cos((count*(math.acos(X))))))
            count+=1    
        return TempK

