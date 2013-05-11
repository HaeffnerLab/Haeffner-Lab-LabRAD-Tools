#    def GetAcquisitionTimings(self):
#        exposure   = c_float()
#        accumulate = c_float()
#        kinetic    = c_float()
#        error = self.dll.GetAcquisitionTimings(byref(exposure),byref(accumulate),byref(kinetic))
#        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
#            return [exposure.value, accumulate.value, kinetic.value]      
#        else:
#            return [sys._getframe().f_code.co_name, ERROR_CODE[error]]
#
#    def SetNumberAccumulations(self, number):
#        error = self.dll.SetNumberAccumulations(number)
#        return [sys._getframe().f_code.co_name, ERROR_CODE[error]]
#            
#    def SetAccumulationCycleTime(self, time):
#        error = self.dll.SetAccumulationCycleTime(c_float(time))
#        return [sys._getframe().f_code.co_name, ERROR_CODE[error]]
#
#    def SetShutter(self, typ, mode, closingtime, openingtime):
#        error = self.dll.SetShutter(typ, mode, closingtime, openingtime)
#        return [sys._getframe().f_code.co_name, ERROR_CODE[error]]
#
#    def SetCoolerMode(self, mode):
#        error = self.dll.SetCoolerMode(mode)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def SaveAsBmp(self, path):
#        im=Image.new("RGB",(self.height,self.width),"white")
#        #im=Image.new("RGB",(512,512),"white")
#        pix = im.load()
#        for i in range(len(self.imageArray)):
#            (row, col) = divmod(i,self.width)
#            picvalue = int(round(self.imageArray[i]*255.0/65535))
#            pix[row,col] = (picvalue,picvalue,picvalue)
#            
#    def SetEMCCDGainMode(self, gainMode):
#        error = self.dll.SetEMCCDGainMode(gainMode)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]   
#    def SetImageRotate(self, iRotate):
#        error = self.dll.SetImageRotate(iRotate)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#
#    def SaveAsBmpNormalised(self, path):
#
#        im=Image.new("RGB",(512,512),"white")
#        pix = im.load()
#
#        maxIntensity = max(self.imageArray)
#
#        for i in range(len(self.imageArray)):
#            (row, col) = divmod(i,self.width)
#            picvalue = int(round(self.imageArray[i]*255.0/maxIntensity))
#            pix[row,col] = (picvalue,picvalue,picvalue)
#
#        im.save(path,"BMP")
#        
#    def SaveAsFITS(self, filename, type):
#        error = self.dll.SaveAsFITS(filename, type)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def GetAccumulationProgress(self):
#        acc = c_long()
#        series = c_long()
#        error = self.dll.GetAcquisitionProgress(byref(acc),byref(series))
#        if ERROR_CODE[error] == "DRV_SUCCESS":
#            return acc.value
#        else:
#            return None
#
#    def SetEMAdvanced(self, gainAdvanced):
#        error = self.dll.SetEMAdvanced(gainAdvanced)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def GetEMGainRange(self):
#        low = c_int()
#        high = c_int()
#        error = self.dll.GetEMGainRange(byref(low),byref(high))
#        self.gainRange = (low.value, high.value)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#      
#    def GetNumberADChannels(self):
#        noADChannels = c_int()
#        error = self.dll.GetNumberADChannels(byref(noADChannels))
#        self.noADChannels = noADChannels.value
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def GetBitDepth(self):
#        bitDepth = c_int()
#
#        self.bitDepths = []
#
#        for i in range(self.noADChannels):
#            self.dll.GetBitDepth(i,byref(bitDepth))
#            self.bitDepths.append(bitDepth.value)
#
#    def SetADChannel(self, index):
#        error = self.dll.SetADChannel(index)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        self.channel = index
#        return ERROR_CODE[error]  
#        
#    def SetOutputAmplifier(self, index):
#        error = self.dll.SetOutputAmplifier(index)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        self.outamp = index
#        return ERROR_CODE[error]
#        
#    def GetNumberHSSpeeds(self):
#        noHSSpeeds = c_int()
#        error = self.dll.GetNumberHSSpeeds(self.channel, self.outamp, byref(noHSSpeeds))
#        self.noHSSpeeds = noHSSpeeds.value
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def GetHSSpeed(self):
#        HSSpeed = c_float()
#
#        self.HSSpeeds = []
#
#        for i in range(self.noHSSpeeds):
#            self.dll.GetHSSpeed(self.channel, self.outamp, i, byref(HSSpeed))
#            self.HSSpeeds.append(HSSpeed.value)
#            
#    def SetHSSpeed(self, index):
#        error = self.dll.SetHSSpeed(index)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        self.hsspeed = index
#        return ERROR_CODE[error]
#        
#    def GetNumberVSSpeeds(self):
#        noVSSpeeds = c_int()
#        error = self.dll.GetNumberVSSpeeds(byref(noVSSpeeds))
#        self.noVSSpeeds = noVSSpeeds.value
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def GetVSSpeed(self):
#        VSSpeed = c_float()
#
#        self.VSSpeeds = []
#
#        for i in range(self.noVSSpeeds):
#            self.dll.GetVSSpeed(i,byref(VSSpeed))
#            self.preVSpeeds.append(VSSpeed.value)
#
#    def SetVSSpeed(self, index):
#        error = self.dll.SetVSSpeed(index)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        self.vsspeed = index
#        return ERROR_CODE[error] 
#    
#    def GetNumberPreAmpGains(self):
#        noGains = c_int()
#        error = self.dll.GetNumberPreAmpGains(byref(noGains))
#        self.noGains = noGains.value
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#
#    def GetPreAmpGain(self):
#        gain = c_float()
#
#        self.preAmpGain = []
#
#        for i in range(self.noGains):
#            self.dll.GetPreAmpGain(i,byref(gain))
#            self.preAmpGain.append(gain.value)
#
#    def SetPreAmpGain(self, index):
#        error = self.dll.SetPreAmpGain(index)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        self.preampgain = index
#        return ERROR_CODE[error]
#        
#    def SetFrameTransferMode(self, frameTransfer):
#        error = self.dll.SetFrameTransferMode(frameTransfer)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#        
#    def SetShutterEx(self, typ, mode, closingtime, openingtime, extmode):
#        error = self.dll.SetShutterEx(typ, mode, closingtime, openingtime, extmode)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]
#        
#    def SetSpool(self, active, method, path, framebuffersize):
#        error = self.dll.SetSpool(active, method, c_char_p(path), framebuffersize)
#        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
#        return ERROR_CODE[error]