from ctypes import c_long, c_buffer, c_float, windll, pointer
from APT_config import stageConfiguration

aptdll = windll.LoadLibrary('APT.dll')
aptdll.APTInit()
config = stageConfiguration()
HWType = c_long(31)

### select the device
serialNumber = 83833535L
HWSerialNum = c_long(serialNumber)
# make sure we cann get stage axis info
minimumPosition = c_float()
maximumPosition = c_float()
units = c_long()
pitch = c_float()
aptdll.MOT_GetStageAxisInfo(HWSerialNum, pointer(minimumPosition), pointer(maximumPosition), pointer(units), pointer(pitch))
stageAxisInformation = [minimumPosition.value, maximumPosition.value, units.value, pitch.value]
print stageAxisInformation

# now try to get position
position = c_float()
aptdll.MOT_GetPosition(HWSerialNum, pointer(position))
print position.value
