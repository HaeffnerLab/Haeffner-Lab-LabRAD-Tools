# InjectionLock_Server

This is the server for implementing the injection lock of 729nm laser light on Raspberry Pi 2.

The IP address of Raspberry Pi is 192.168.169.162 and connect to conferencewifi2015. 

Do not use the same address! If change the password for wifi, remember to tell Raspberry Pi!

To chagne the wifi password:

First, login into it!
```
ssh pi@192.168.169.162
```
password is raspberry

Second, login into a file saving the setting of network
```
sudo emacs /etc/wpa_supplicant/wpa_supplicant.conf
```
Then, change the password of wifi here.


# How to relock lasers?
Use your terminal to connect the server in laser room. 
```
ipython
import labrad
cxn = labrad.connect('192.168.169.49', password='lab', tls_mode='off')
inj = cxn.injectionlock
```
Then just relock the laser
```
inj.relock_supervisor()
```
or
```
inj.relock_slave()
```
These two methods will scan the current of supervisor and slave. 

The default scan range is from 0.1-2.9V for supervisor and 0.1-5.1V for slave.

If you want to change the scan range, then input the range you want to the method, like:
```
inj.relock_supervisor(1.2,3.4)
```
Then it will scan the current of supervisor from 1.2-3.4. Same for slave.
# About the code
It consists of three parts.
### model.py
model.py is a file in a existing python project named Freqshow on Raspberry. It controls the USB dongles connecting to Raspberry Pi to take data and make a FFT to the data.

You could change "center frequency" at line 44 (now is 80MHz) and "scan range" at line 45 (now is 1MHz) in model.py
```
self.set_center_freq(80.0)
self.set_sample_rate(1.0)
```
Do not input large number here. The USB dongles cannot hold the center frequency larger than GHz, and scan range larger than 4MHz.
### Injectionlock_Server.py
Injectionlock_Server.py is the core file. 

First, it scan the current of the laser you want to relock, then get the data in frequency domain. 
```
for v in scan1:
    yield self.dac.set_individual_analog_voltages([('05', v)])
```
Second, change the data (now is log axis, in dBm unit) into linear axis, then calculate integration of signal at each current set.
```
def linearize(self,dbm)
def get_signal_integration(self,data)
```
Third, use moving average to signal_integration to ease the fluctuation. 
```
def get_moving_ave(self,signal_integration)
```
Finally, find the locking point and set to it.
```
def get_supervisor_locking_point(self,signal_integration)
```

All data will save at /home/pi/Desktop/InjectionLockingData

I use sshfs to mount this folder to a folder on our server: /home/pi/data (on the server)

The result will show under the tab "Injection lock" on our website (192.168.169.13). 

The website will updata every 5 mins.
### config.py
config.py is the setting file. Some important variables are set here.

# About the new beat note setup
The beat note is between master(red fiber) and supervisor(orange fiber).
A halfwave plate is fixed to change the polarization.







