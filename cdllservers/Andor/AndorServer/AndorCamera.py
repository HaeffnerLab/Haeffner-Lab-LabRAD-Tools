import ctypes as c
from configuration import andor_configuration as config
import os

'''Adoped from https://code.google.com/p/pyandor/'''

class AndorInfo(object):
    
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
        
               
class AndorCamera(object):
    """
    Andor class which is meant to provide the Python version of the same
    functions that are defined in the Andor's SDK. Since Python does not
    have pass by reference for immutable variables, some of these variables
    are actually stored in the class instance. For example the temperature,
    gain, gainRange, status etc. are stored in the class.
    """
    
    def __init__(self):
        try:
            print 'Loading DLL'
            self.dll = c.windll.LoadLibrary(config.path_to_dll)
            print 'Initializing Camera'
            error = self.dll.Initialize(os.path.dirname(__file__))
            print 'Done Initializing, {}'.format(ERROR_CODE[error])
            self.info = AndorInfo()
            self.get_detector_dimensions()
            self.get_temperature_range()
            self.acquire_camera_serial_number()
            self.get_camera_em_gain_range()
            self.get_emccd_gain()
            self.set_read_mode(config.read_mode)
            self.set_acquisition_mode(config.acquisition_mode)
            self.set_trigger_mode(config.trigger_mode)
            self.set_exposure_time(config.exposure_time)
            #set image to full size with the default binning
            self.set_image(config.binning[0], config.binning[0], 1, self.info.width, 1, self.info.height)
            self.set_cooler_on()
            self.set_temperature(config.set_temperature)
            self.get_cooler_state()
            self.get_temperature()
        except Exception as e:
            print 'Error Initializing Camera', e

    def print_get_software_version(self):
        '''
        gets the version of the SDK
        '''
        eprom = c.c_int()
        cofFile = c.c_int()
        vxdRev = c.c_int()
        vxdVer = c.c_int()
        dllRev = c.c_int()
        dllVer = c.c_int()
        self.dll.GetSoftwareVersion(c.byref(eprom), c.byref(cofFile), c.byref(vxdRev), c.byref(vxdVer),  c.byref(dllRev), c.byref(dllVer))
        print 'Software Version'
        print eprom
        print cofFile
        print vxdRev
        print vxdVer
        print dllRev
        print dllVer
        
    def print_get_capabilities(self):
        '''
        gets the exact capabilities of the camera
        '''
        
        class AndorCapabilities(c.Structure):
            _fields_ = [('ulSize', c.c_ulong),
                        ('ulAcqModes', c.c_ulong),
                        ('ulReadModes', c.c_ulong),
                        ('ulTriggerModes', c.c_ulong),
                        ('ulCameraType', c.c_ulong),
                        ('ulPixelMode', c.c_ulong),
                        ('ulSetFunctions', c.c_ulong),
                        ('ulGetFunctions', c.c_ulong),
                        ('ulFeatures', c.c_ulong),
                        ('ulPCICard', c.c_ulong),
                        ('ulEMGainCapability', c.c_ulong),
                        ('ulFTReadModes', c.c_ulong),
                        ]
        caps = AndorCapabilities()
        caps.ulSize = c.c_ulong(c.sizeof(caps))
        error = self.dll.GetCapabilities(c.byref(caps))
        print 'ulAcqModes',         '{:07b}'.format(caps.ulAcqModes)
        print 'ulReadModes',        '{:06b}'.format(caps.ulReadModes)
        print 'ulTriggerModes',     '{:08b}'.format(caps.ulTriggerModes)
        print 'ulCameraType',       '{}'.format(caps.ulCameraType)
        print 'ulPixelMode',        '{:032b}'.format(caps.ulPixelMode)
        print 'ulSetFunctions',     '{:025b}'.format(caps.ulSetFunctions)
        print 'ulGetFunctions',     '{:016b}'.format(caps.ulGetFunctions)
        print 'ulFeatures',         '{:020b}'.format(caps.ulFeatures)
        print 'ulPCICard',          '{}'.format(caps.ulPCICard)
        print 'ulEMGainCapability', '{:020b}'.format(caps.ulEMGainCapability)
        print 'ulFTReadModes',      '{:06b}'.format(caps.ulFTReadModes)
        
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

    def shut_down(self):
        error = self.dll.ShutDown()
        return ERROR_CODE[error]
    
ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXNOTINSTALLED",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_ERROR_VXD_INIT",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20013: "DRV_ERROR_ACK",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20034: "DRV_TEMP_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMP_STABILIZED",
    20037: "DRV_TEMP_NOT_REACHED",
    20038: "DRV_TEMP_OUT_RANGE",
    20039: "DRV_TEMP_NOT_SUPPORTED",
    20040: "DRV_TEMP_DRIFT",
    20050: "DRV_COF_NOTLOADED",
    20053: "DRV_FLEXERROR",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20083: "P7_INVALID",
    20089: "DRV_USBERROR",
    20091: "DRV_NOT_SUPPORTED",
    20099: "DRV_BINNING_ERROR",
    20990: "DRV_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE"
}

READ_MODE = {
    'Full Vertical Binning':0,
    'Multi-Track':1,
    'Random-Track':2,
    'Sinle-Track':3,
    'Image':4
                }

AcquisitionMode = {
    'Single Scan':1,
    'Accumulate':2,
    'Kinetics':3,
    'Fast Kinetics':4,
    'Run till abort':5
                   }

TriggerMode = {
    'Internal':0,
    'External':1,
    'External Start':6,
    'External Exposure':7,
    'External FVB EM':9,
    'Software Trigger':10,
    'External Charge Shifting':12
               }

if __name__ == '__main__':
    camera = AndorCamera()