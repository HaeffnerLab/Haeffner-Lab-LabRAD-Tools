cd /
/bin/sleep 10
sudo umount /home/pi/Desktop/InjectonLockingData
sshfs pi@192.168.169.13:/home/pi/data /home/pi/Desktop/InjectionLockingData
cd home/pi/Injectionlock_Server
#set for connecting to laser server
export LABRADPASSWORD=lab
export LABRADHOST=192.168.169.49
export LABRAD_TLS=off
python Injectionlock_Server.py
cd /
