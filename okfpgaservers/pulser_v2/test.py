import ok
xem = ok.FrontPanel()
xem.OpenBySerial("")
xem.GetDeviceID()
xem.ConfigureFPGA("cctphoton.bit")

xem.ActivateTriggerIn(0x40, 4) # reset

# set ch 0
xem.SetWireInValue(0x04, 0x00)
xem.UpdateWireIns()

xem.WriteToBlockPipeIn(0x81, 2, '\x00\x00\xff\xff\xff\xff\xff\x7f') # 225 mhz
#xem.WriteToBlockPipeIn(0x81, 2, "\x00\x00\xff\xff\x00\x00\x00\x48") #225
xem.WriteToBlockPipeIn(0x81,2,"\x00\x00")

# switch to ch 1

#xem.SetWireInValue(0x04, 0x01)
#xem.UpdateWireIns()

#xem.WriteToBlockPipeIn(0x81, 2, "\x00\x00\xef\xff\x00\x00\x00\x30")
#xem.WriteToBlockPipeIn(0x81, 2, "\x00\x00\xef\xff\x00\x00\x00\x38")
#xem.WriteToBlockPipeIn(0x81, 2, "\x00\x00")
