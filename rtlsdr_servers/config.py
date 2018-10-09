# screen resolution setting, first is the length one set of data you take, which is no more than 1022
first = 960
second = 800

# scan range of supervisor
v_min_supervisor = 0.1
v_max_supervisor = 2.9
scan_steps = 100
# scan range of slave
v_min_slave = 0.1
v_max_slave = 5.1

# data_time is the average times that use for taking data when scanning
data_time = 10

# moving average point
aver_point = int(scan_steps*0.1/2)*2+1
