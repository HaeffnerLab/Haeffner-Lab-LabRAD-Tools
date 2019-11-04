import ctypes as c
from configuration import nuvu_configuration as config
import os
from NuvuErrors import NuvuErrors

class NuvuInfo(object):
    def __init__(self):
        self.width                  = None
        self.height                 = None
        self.min_gain               = None
        self.max_gain               = None
        self.emccd_gain             = None
        self.trigger_mode           = None
        self.exposure_time          = None
        self.readout_time           = None
        self.waiting_time           = None
        self.image_region           = None
        self.number_kinetics        = None
        
class NuvuCamera():
    def __init__(self):
        try:
            print('Initializing Nuvu Camera...')
            self.info = NuvuInfo()
            self.dll = c.CDLL(config.path_to_dll)
            
            self.ncCam = c.pointer(c.c_long())
            error = self.dll.ncCamOpen(NC_AUTO_UNIT, NC_AUTO_CHANNEL, 4, c.byref(self.ncCam))
            if not SUCCESS(error):
                raise Exception(ERROR_DESCRIPTION(error))
            
            error = self.dll.ncCamSetReadoutMode(self.ncCam, 1)
            if not SUCCESS(error):
                raise Exception(ERROR_DESCRIPTION(error))

            print('Nuvu Camera opened successfully', self.ncCam)

            self.get_detector_dimensions()
            self.get_camera_em_gain_range()
            self.set_trigger_mode(config.trigger_mode)
            self.set_exposure_time(config.exposure_time)
            self.set_emccd_gain(config.em_gain)
            self.set_image(config.binning[0], config.binning[1], 1, self.info.width, 1, self.info.height)
            print('Nuvu Camera initialized successfully')
            print('width', self.info.width)
            print('height', self.info.height)
            print('min_gain', self.info.min_gain)
            print('max_gain', self.info.max_gain)
            print('emccd_gain', self.info.emccd_gain)
            print('trigger_mode', self.info.trigger_mode)
            print('exposure_time', self.info.exposure_time)
            print('image_region', self.info.image_region)
            print('number_kinetics', self.info.number_kinetics)
        except Exception as e:
            print('Error initializing Nuvu Camera:', e)
            return
        
    def get_detector_dimensions(self):
        '''
        gets the dimensions of the detector
        '''
        detector_width = c.c_int()
        detector_height = c.c_int()
        error = self.dll.ncCamGetMaxSize(self.ncCam, c.byref(detector_width), c.byref(detector_height))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.info.width = detector_width.value
        self.info.height = detector_height.value
        return [self.info.width, self.info.height]
    
    def get_camera_em_gain_range(self):
        min_gain = c.c_int()
        max_gain = c.c_int()
        error = self.dll.ncCamGetRawEmGainRange(self.ncCam, c.byref(min_gain), c.byref(max_gain))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.info.min_gain = min_gain.value
        self.info.max_gain = max_gain.value
        return (min_gain.value, max_gain.value)
        
    def get_emccd_gain(self):
        gain = c.c_int()
        error = self.dll.ncCamGetRawEmGain(self.ncCam, 1, c.byref(gain))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.info.emccd_gain = gain.value
        return gain.value
        
    def set_emccd_gain(self, gain):
        error = self.dll.ncCamSetRawEmGain(self.ncCam, c.c_int(int(gain)))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.info.emccd_gain = gain
    
    def set_acquisition_mode(self, mode):
        # not needed for Nuvu camera
        pass
    
    def get_acquisition_mode(self):
        # not needed for Nuvu camera
        return 'N/A'
    
    def set_trigger_mode(self, mode):
        try:
            mode_number = TriggerMode[mode]
        except KeyError:
            raise Exception("Incorrect trigger mode {}".format(mode))
        frames_per_trigger = 1
        error = self.dll.ncCamSetTriggerMode(self.ncCam, mode_number, frames_per_trigger)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.info.trigger_mode = mode
    
    def get_trigger_mode(self):
        return self.info.trigger_mode
    
    def set_exposure_time(self, time):
        exposure_time_in_ms = c.c_double(time * 1000.)
        error = self.dll.ncCamSetExposureTime(self.ncCam, exposure_time_in_ms)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.get_acquisition_timings()
    
    def get_exposure_time(self):
        return self.info.exposure_time
    
    def get_acquisition_timings(self):
        exposure_time_in_ms = c.c_double()
        error = self.dll.ncCamGetExposureTime(self.ncCam, 0, c.byref(exposure_time_in_ms))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        readout_time_in_ms = c.c_double()
        error = self.dll.ncCamGetReadoutTime(self.ncCam, c.byref(readout_time_in_ms))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        waiting_time_in_ms = c.c_double(0.1 * readout_time_in_ms.value)
        error = self.dll.ncCamSetWaitingTime(self.ncCam, waiting_time_in_ms)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))
        
        self.info.exposure_time = exposure_time_in_ms.value / 1000.
        self.info.readout_time = readout_time_in_ms.value / 1000.
        self.info.waiting_time = waiting_time_in_ms.value / 1000.
        
    def set_image(self, hbin, vbin, hstart, hend, vstart, vend):
        is_acquiring = self.is_acquiring()
        if is_acquiring:
            self.abort_acquisition()

        start_x = int(hstart-1); end_x = int(hend-1); start_y = int(vstart-1); end_y = int(vend-1)
        error = self.dll.ncCamSetRoi(self.ncCam, start_x, end_x, start_y, end_y)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        bin_x = int(hbin); bin_y = int(vbin)
        error = self.dll.ncCamSetBinningMode(self.ncCam, bin_x, bin_y)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        self.info.image_region = [hbin, vbin, hstart, hend, vstart, vend]

        if is_acquiring:
            self.start_acquisition()
    
    def get_image(self):
        return self.info.image_region
    
    def start_acquisition(self):
        error = self.dll.ncCamSetShutterMode(self.ncCam, SHUTTER_OPEN)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        error = self.dll.ncCamStart(self.ncCam, self.info.number_kinetics)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))
    
    def wait_for_acquisition(self):
        # Loop until the camera is no longer in acquisition mode
        is_acquiring = True
        while is_acquiring:
            is_acquiring = self.is_acquiring()

    def is_acquiring(self):
        is_acquiring = c.c_int()
        error = self.dll.ncCamIsAcquiring(self.ncCam, c.byref(is_acquiring))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))
        return is_acquiring.value != 0
    
    def abort_acquisition(self):
        error = self.dll.ncCamAbort(self.ncCam)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

    def get_acquired_data(self, num_images):
        hbin, vbin, hstart, hend, vstart, vend = self.info.image_region
        dim = int( ( hend - hstart + 1 ) * (vend - vstart + 1) / float(hbin * vbin) )
        images = []
        for i in range(num_images):
            image_struct = c.c_uint32 * dim
            image = image_struct()
            error = self.dll.ncCamReadUInt32(self.ncCam, c.pointer(image))
            if not SUCCESS(error):
                raise Exception(ERROR_DESCRIPTION(error))
            images.extend(image[:])
        return images
    
    def get_most_recent_image(self):
        return self.get_acquired_data(num_images=1)

    def set_number_kinetics(self, numKin):
        self.info.number_kinetics = numKin
    
    def get_number_kinetics(self):
        return self.info.number_kinetics

    # def get_status(self):
    #     # TODO: implement using Nuvu APIs, if needed for debugging
    #     status = c.c_int()
    #     error = self.dll.GetStatus(c.byref(status))
    #     if (ERROR_CODE[error] == 'DRV_SUCCESS'):
    #         return ERROR_CODE[status.value]      
    #     else:
    #         raise Exception(ERROR_CODE[error])
         
    # def get_series_progress(self):
    #     # TODO: implement using Nuvu APIs, if needed for debugging
    #     acc = c.c_long()
    #     series = c.c_long()
    #     error = self.dll.GetAcquisitionProgress(c.byref(acc),c.byref(series))
    #     if ERROR_CODE[error] == "DRV_SUCCESS":
    #         return acc.value, series.value
    #     else:
    #         raise Exception(ERROR_CODE[error])

    def shut_down(self):
        error = self.dll.ncCamAbort(self.ncCam)
        if not SUCCESS(error):
            print(ERROR_DESCRIPTION(error))
            return ERROR_DESCRIPTION(error)

        error = self.dll.ncCamSetShutterMode(self.ncCam, SHUTTER_CLOSE)
        if not SUCCESS(error):
            print(ERROR_DESCRIPTION(error))
            return ERROR_DESCRIPTION(error)

        error = self.dll.ncCamClose(self.ncCam)
        if not SUCCESS(error):
            print(ERROR_DESCRIPTION(error))
            return ERROR_DESCRIPTION(error)

        print('Nuvu Camera shut down successfully')
        return 'Nuvu Camera shut down successfully'
        
    def nuvu_test(self):
        #
        # TEST CODE - based on "Simple Acquisition" and "Exposure and Trigger" samples from Nuvu SDK
        #
        error = self.dll.ncCamSetReadoutMode(self.ncCam, 1)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        readoutTimeInMs = c.c_double()
        error = self.dll.ncCamGetReadoutTime(self.ncCam, c.byref(readoutTimeInMs))
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        exposureTimeInMs = readoutTimeInMs
        error = self.dll.ncCamSetExposureTime(self.ncCam, exposureTimeInMs)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        waitingTimeInMs = c.c_double(0.1 * exposureTimeInMs.value)
        error = self.dll.ncCamSetWaitingTime(self.ncCam, waitingTimeInMs)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        # timeout needs to be long enough to receive each trigger
        triggerTimeoutInMs = 1000
        timeoutInMs = c.c_int(int(waitingTimeInMs.value + readoutTimeInMs.value + exposureTimeInMs.value + triggerTimeoutInMs))
        error = self.dll.ncCamSetTimeout(self.ncCam, timeoutInMs)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        numFramesPerTrigger = 1
        triggerMode = TriggerMode['EXT_LOW_HIGH']
        error = self.dll.ncCamSetTriggerMode(self.ncCam, triggerMode, numFramesPerTrigger)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        error = self.dll.ncCamSetShutterMode(self.ncCam, SHUTTER_OPEN)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        numImages = 5
        error = self.dll.ncCamStart(self.ncCam, numImages)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        # Loop in which acquired images are read
        for i in range(numImages):
            print('Ready for trigger!')

            myNcImage = c.pointer(c.c_ushort())
            error = self.dll.ncCamRead(self.ncCam, c.byref(myNcImage))
            if not SUCCESS(error):
                raise Exception(ERROR_DESCRIPTION(error))
            print('Image successfully read from camera', myNcImage)

            imageName = c.c_char_p("Image" + str(i))
            headerComment = c.c_char_p("Acquisition test")
            saveFormat = IMAGEFORMAT_TIF
            error = self.dll.ncCamSaveImage(self.ncCam, myNcImage, imageName, saveFormat, headerComment, 1)
            if not SUCCESS(error):
                raise Exception(ERROR_DESCRIPTION(error))

            print('Saved image', imageName.value + ".tif")
        
        error = self.dll.ncCamSetShutterMode(self.ncCam, SHUTTER_CLOSE)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

        #
        # cleanUp() from utility.c
        #
        error = self.dll.ncCamClose(self.ncCam)
        if not SUCCESS(error):
            raise Exception(ERROR_DESCRIPTION(error))

def SUCCESS(error_code):
    return error_code == 0

def ERROR_DESCRIPTION(error_code):
    for description, code in NuvuErrors.items():
        if error_code == code:
            return description
    return "Error code " + str(error_code)
    
NC_AUTO_DETECT = 0x0000ffff
NC_AUTO_CHANNEL = NC_AUTO_DETECT
NC_AUTO_UNIT = 0x6fffffff
NC_FULL_WIDTH = -1
NC_FULL_HEIGHT = -1
NC_USE_MAC_ADRESS = 0x20000000

SHUTTER_NOT_SET = 0
SHUTTER_OPEN = 1
SHUTTER_CLOSE = 2
SHUTTER_AUTO = 3
SHUTTER_BIAS_DEFAULT = SHUTTER_CLOSE

IMAGEFORMAT_UNKNOWN = -1
IMAGEFORMAT_TIF = 0
IMAGEFORMAT_FITS = 1

TriggerMode = {
    'CONT_HIGH_LOW': -3,
    'EXT_HIGH_LOW_EXP': -2,
    'EXT_HIGH_LOW': -1,
    'INTERNAL': 0,
    'EXT_LOW_HIGH': 1,
    'EXT_LOW_HIGH_EXP': 2,
    'CONT_LOW_HIGH': 3
}
    
if __name__ == '__main__':
    camera = None
    try:
        camera = NuvuCamera()
        #camera.nuvu_test()
    except Exception as e:
        if camera:
            camera.shut_down()
        raise
    if camera:
        camera.shut_down()
