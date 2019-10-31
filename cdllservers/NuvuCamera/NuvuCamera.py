import ctypes as c
import os

class NuvuInfo(object):
    def __init__(self):
        self.width                  = None
        self.height                 = None
        self.min_temp               = None
        self.max_temp               = None
        self.cooler_state           = None
        self.temperature_setpoint   = None
        self.temperature            = None
        self.serial_number          = None
        self.min_gain               = None
        self.max_gain               = None
        self.emccd_gain             = None
        self.read_mode              = None
        self.acquisition_mode       = None
        self.trigger_mode           = None
        self.exposure_time          = None
        self.accumulate_cycle_time  = None
        self.kinetic_cycle_time     = None
        self.image_region           = None
        self.number_kinetics        = None
		
class NuvuCamera():
    def __init__(self):
        self.dll = c.windll.LoadLibrary("Nuvu.dll")
        self.dll.initialize()
        print 'Nuvu Camera initialized'
        self.info = NuvuInfo()
		
	'''
	The following functions are called in pulse_sequence.py:
	
		abort_acquisition()
		get_acquired_data(self.N)
		get_exposure_time()
		get_trigger_mode()
		set_image_region(*self.image_region)
		set_acquisition_mode("Kinetics")
		set_exposure_time(self.initial_exposure)
		set_image_region(1, 1, 1, 658, 1, 496)
		set_number_kinetics(self.N)
		set_trigger_mode("External")
		start_acquisition()
		start_live_display()
		wait_for_kinetic()
	
	'''
    
	def get_detector_dimensions(self):
        '''
        gets the dimensions of the detector
        '''
        detector_width = c.c_int()
        detector_height = c.c_int()
        self.dll.GetDetector(c.byref(detector_width), c.byref(detector_height))
        self.info.width = detector_width.value
        self.info.height = detector_height.value
        return [self.info.width, self.info.height]
        
    def get_temperature_range(self):
        '''
        gets the range of available temperatures
        '''
        min_temp = c.c_int()
        max_temp = c.c_int()
        self.dll.GetTemperatureRange(c.byref(min_temp), c.byref(max_temp))
        self.info.min_temp = min_temp.value
        self.info.max_temp = max_temp.value
        return [self.info.min_temp, self.info.max_temp]
        
    def get_cooler_state(self):
        '''
        reads the state of the cooler
        '''
        cooler_state = c.c_int()
        error = self.dll.IsCoolerOn(c.byref(cooler_state))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.cooler_state = bool(cooler_state)
            return self.info.cooler_state
        else:
            raise Exception(ERROR_CODE[error])
        
    def set_cooler_on(self):
        '''
        turns on cooling
        '''
        error = self.dll.CoolerON()
        if not (ERROR_CODE[error] == 'DRV_SUCCESS'):
            raise Exception(ERROR_CODE[error])

    def set_cooler_off(self):
        '''
        turns off cooling
        '''
        error = self.dll.CoolerOFF()
        if not (ERROR_CODE[error] == 'DRV_SUCCESS'):
            raise Exception(ERROR_CODE[error])

    def get_temperature(self):
        temperature = c.c_int()
        error = self.dll.GetTemperature(c.byref(temperature))
        if (ERROR_CODE[error] == 'DRV_TEMP_STABILIZED' or ERROR_CODE[error] == 'DRV_TEMP_NOT_REACHED' or ERROR_CODE[error] == 'DRV_TEMP_DRIFT' or ERROR_CODE[error] == 'DRV_TEMP_NOT_STABILIZED'):
            self.info.temperature = temperature.value
            return temperature.value
        else:
            raise Exception(ERROR_CODE[error])

    def set_temperature(self, temperature):
        temperature = c.c_int(int(temperature))
        error = self.dll.SetTemperature( temperature )
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.temperature_setpoint = temperature.value
        else:
            raise Exception(ERROR_CODE[error])
        
    def acquire_camera_serial_number(self):
        serial_number = c.c_int()
        error = self.dll.GetCameraSerialNumber(c.byref(serial_number))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.serial_number = serial_number.value
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_camera_serial_number(self):
        return self.info.serial_number
    
    def get_camera_em_gain_range(self):
        min_gain = c.c_int()
        max_gain = c.c_int()
        error = self.dll.GetEMGainRange(c.byref(min_gain), c.byref(max_gain))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.min_gain = min_gain.value
            self.info.max_gain = max_gain.value
            return (min_gain.value, max_gain.value)
        else:
            raise Exception(ERROR_CODE[error])
        
    def get_emccd_gain(self):
        gain = c.c_int()
        error = self.dll.GetEMCCDGain(c.byref(gain))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.emccd_gain = gain.value
            return gain.value
        else:
            raise Exception(ERROR_CODE[error])
        
    def set_emccd_gain(self, gain):
        error = self.dll.SetEMCCDGain(c.c_int(int(gain)))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.emccd_gain = gain             
        else:
            raise Exception(ERROR_CODE[error])
    
    def set_read_mode(self, mode):
        try:
            mode_number = READ_MODE[mode]
        except KeyError:
            raise Exception("Incorrect read mode {}".format(mode))
        error = self.dll.SetReadMode(c.c_int(mode_number))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.read_mode = mode
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_read_mode(self):
        return self.info.read_mode
    
    def set_acquisition_mode(self, mode):
        try:
            mode_number = AcquisitionMode[mode]
        except KeyError:
            raise Exception("Incorrect acquisition mode {}".format(mode))
        error = self.dll.SetAcquisitionMode(c.c_int(mode_number))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.acquisition_mode = mode      
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_acquisition_mode(self):
        return self.info.acquisition_mode
    
    def set_trigger_mode(self, mode):
        try:
            mode_number = TriggerMode[mode]
        except KeyError:
            raise Exception("Incorrect trigger mode {}".format(mode))
        error = self.dll.SetTriggerMode(c.c_int(mode_number))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.trigger_mode = mode
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_trigger_mode(self):
        return self.info.trigger_mode
    
    def set_exposure_time(self, time):
        error = self.dll.SetExposureTime(c.c_float(time))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.get_acquisition_timings()   
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_exposure_time(self):
        return self.info.exposure_time
    
    def get_acquisition_timings(self):
        exposure = c.c_float()
        accumulate = c.c_float()
        kinetic = c.c_float()
        error = self.dll.GetAcquisitionTimings(c.byref(exposure), c.byref(accumulate), c.byref(kinetic))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.exposure_time = exposure.value
            self.info.accumulate_cycle_time = accumulate.value
            self.info.kinetic_cycle_time = kinetic.value
        else:
            raise Exception(ERROR_CODE[error])
        
    def set_image(self, hbin, vbin, hstart, hend, vstart, vend):
        hbin = int(hbin); vbin = int(vbin); hstart = int(hstart); hend = int(hend); vstart = int(vstart); vend = int(vend)
        error = self.dll.SetImage(c.c_int(hbin), c.c_int(vbin), c.c_int(hstart), c.c_int(hend), c.c_int(vstart), c.c_int(vend))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.image_region = [hbin, vbin, hstart, hend, vstart, vend]
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_image(self):
        return self.info.image_region
    
    def start_acquisition(self):
        error = self.dll.StartAcquisition()
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            return
        else:
            raise Exception(ERROR_CODE[error])
    
    def wait_for_acquisition(self):
        error = self.dll.WaitForAcquisition()
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            return
        else:
            raise Exception(ERROR_CODE[error])
    
    def abort_acquisition(self):
        error = self.dll.AbortAcquisition()
        if (ERROR_CODE[error] in ['DRV_SUCCESS', 'DRV_IDLE']):
            return
        else:
            raise Exception(ERROR_CODE[error])

    def get_acquired_data(self, num_images):  
        hbin, vbin, hstart, hend, vstart, vend = self.info.image_region
        dim = ( hend - hstart + 1 ) * (vend - vstart + 1) / float(hbin * vbin)
        dim = int(num_images * dim)
        image_struct = c.c_int * dim
        image = image_struct()
        error = self.dll.GetAcquiredData(c.pointer(image),dim)
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            image = image[:]
            return image
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_most_recent_image(self):  
        hbin, vbin, hstart, hend, vstart, vend = self.info.image_region
        dim = ( hend - hstart + 1 ) * (vend - vstart + 1) / float(hbin * vbin)
        dim = int(dim)
        image_struct = c.c_int * dim
        image = image_struct()
        error = self.dll.GetMostRecentImage(c.pointer(image),dim)
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            image = image[:]
            return image
        else:
            raise Exception(ERROR_CODE[error])        

    def set_number_kinetics(self, numKin):
        error = self.dll.SetNumberKinetics(c.c_int(int(numKin)))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            self.info.number_kinetics = numKin
        else:
            raise Exception(ERROR_CODE[error])
    
    def get_number_kinetics(self):
        return self.info.number_kinetics

    def get_status(self):
        status = c.c_int()
        error = self.dll.GetStatus(c.byref(status))
        if (ERROR_CODE[error] == 'DRV_SUCCESS'):
            return ERROR_CODE[status.value]      
        else:
            raise Exception(ERROR_CODE[error])
         
    def get_series_progress(self):
        acc = c.c_long()
        series = c.c_long()
        error = self.dll.GetAcquisitionProgress(c.byref(acc),c.byref(series))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return acc.value, series.value
        else:
            raise Exception(ERROR_CODE[error])
    
    def prepare_acqusition(self):
        error = self.dll.PrepareAcquisition()
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return
        else:
            raise Exception(ERROR_CODE[error])

    def shut_down(self):
        error = self.dll.ShutDown()
        return ERROR_CODE[error]
		
if __name__ == '__main__':
    camera = NuvuCamera()
