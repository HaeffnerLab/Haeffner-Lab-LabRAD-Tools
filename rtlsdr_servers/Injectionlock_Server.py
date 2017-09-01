from labrad.server import LabradServer, setting
import model
import config
import numpy as np
import time
from rtlsdr import RtlSdr


SERVERNAME = 'InjectionLock'

class InjectionLock_Server(LabradServer):

    name = SERVERNAME

    def initServer(self):
        self.dac = self.client.servers['laserdac_server']
        # first plug in slave dongle and then plug in supervisor dongle!!!!!!!!!!!
        sdr1 = RtlSdr(device_index=0)
        sdr2 = RtlSdr(device_index=1)
        self.supervisormodel = model.FreqShowModel(config.first,config.second,sdr1)
        self.slavemodel = model.FreqShowModel(config.first,config.second,sdr2)

    @setting(1, min = 'v', max = 'v')
    def relock_supervisor(self,c,min = config.v_min_supervisor,max = config.v_max_supervisor):

        fsmodel = self.supervisormodel

        before_min = config.v_min_supervisor
        before_max = config.v_max_supervisor

        config.v_min_supervisor = min
        config.v_max_supervisor = max

        # Not use first 100 datas, let program run for a while
        for m in range(1000):
            fsmodel.get_data()

        # scan range
        v_min = config.v_min_supervisor
        v_max = config.v_max_supervisor
        steps = config.scan_steps

        index = 0

        # up_data 2-ndarray
        up = [[0 for l in range(config.first)] for l in range(steps)]
        up_data = np.array(up, dtype=np.float64)

        scan1 = np.linspace(v_min, v_max, steps)

        data_time = config.data_time
        temp = [[0 for l in range(config.first)] for l in range(data_time)]
        temp_data = np.array(temp, dtype=np.float64)




        for v in scan1:
            yield self.dac.set_individual_analog_voltages([('05', v)])
            # generate random array --> save somehow
            # get FFT from beatnote
            # save FFT for each voltage setting
            print "scan supervisor: ", v
            time.sleep(0.5)
            for k in range(data_time):
                temp_data[k] = fsmodel.get_data()

            new_data = []
            for k in range(config.first):
                new_data.append(0)

            for p in range(config.first):
                for q in range(data_time):
                    new_data[p] += temp_data[q][p] / data_time
            up_data[index] = new_data

            index += 1

        up_signal_integration = []
        for k in range(len(up_data)):
            up_signal_integration.append(self.get_signal_integration
                                         (self.linearize(up_data[k])))


        up_vol = self.get_up_vol_supervisor()
        up_aver_signal = self.get_moving_ave(up_signal_integration)
        locking_point = self.get_supervisor_locking_point(up_signal_integration)
        self.set_supervisor_current(int(locking_point * 1000) / 1000.0)
        print 'supervisor current is relocked to: ', int(locking_point * 1000) / 1000.0
        print

        signal  =[]
        for length in range(len(up_vol)):
            list = []
            list.append(up_vol[length])
            list.append(up_signal_integration[length])
            signal.append(list)

        # transform and send up_signal_integration and up_scan
        name = time.strftime('%Y-%m-%d %H:%M:%S_', time.localtime(time.time())) \
               + "_" + str(int(locking_point*100)/100.0)+"_signal"
        np.savetxt("/home/pi/Desktop/InjectionLockingData/supervisor/"
                   +name+".csv", signal, delimiter=',')

        config.v_min_supervisor = before_min
        config.v_max_supervisor = before_max

    @setting(2,min = 'v', max = 'v')
    def relock_slave(self,c,min = config.v_min_slave,max = config.v_max_slave):

        fsmodel = self.slavemodel
        # Not use first 100 datas, let program run for a while
        for m in range(1000):
            fsmodel.get_data()

        before_min = config.v_min_slave
        before_max = config.v_max_slave

        config.v_min_slave = min
        config.v_max_slave = max

        # scan range
        v_min = config.v_min_slave
        v_max = config.v_max_slave
        steps = config.scan_steps

        index = 0

        # up_data 2-ndarray
        up = [[0 for l in range(config.first)] for l in range(steps)]
        up_data = np.array(up, dtype=np.float64)

        scan1 = np.linspace(v_min, v_max, steps)

        data_time = config.data_time

        temp = [[0 for l in range(config.first)] for l in range(data_time)]
        temp_data = np.array(temp, dtype=np.float64)

        for v in scan1:
            yield self.dac.set_individual_analog_voltages([('06', int(v*1000)/1000.0)])
            # generate random array --> save somehow
            # get FFT from beatnote
            # save FFT for each voltage setting
            # maybe one for each direction
            print "scan slave: ", v
            time.sleep(1)
            for k in range(data_time):
                temp_data[k] = fsmodel.get_data()

            new_data = []
            for k in range(config.first):
                new_data.append(0)

            for p in range(config.first):
                for q in range(data_time):
                    new_data[p] += temp_data[q][p] / data_time

            up_data[index] = new_data
            index += 1

        up_signal_integration = []
        for k in range(len(up_data)):
            up_signal_integration.append(self.get_signal_integration
                                         (self.linearize(up_data[k])))
        up_vol = self.get_up_vol_slave()
        up_aver_signal = self.get_moving_ave(up_signal_integration)
        # set to the locking point
        locking_point = self.get_slave_locking_point(up_signal_integration)
        self.set_slave_current(int(locking_point * 1000) / 1000.0)
        print 'slave current is relocked to: ', int(locking_point * 1000) / 1000.0
        print


        signal  =[]
        for length in range(len(up_vol)):
            list = []
            list.append(up_vol[length])
            list.append(up_signal_integration[length])
            signal.append(list)

        # transform and send up_signal_integration and up_scan
        name = time.strftime('%Y-%m-%d %H:%M:%S_', time.localtime(time.time())) \
               + "_" + str(int(locking_point*100)/100.0)+"_signal"
        np.savetxt("/home/pi/Desktop/InjectionLockingData/slave/"
                   +name+".csv", signal, delimiter=',')

        config.v_min_slave = before_min
        config.v_max_slave = before_max

    def set_supervisor_current(self,first_current):
        self.dac.set_individual_analog_voltages([('05', first_current)])
        print 'supervisor is set to:',first_current

    def set_slave_current(self,second_current):
        self.dac.set_individual_analog_voltages([('06', second_current)])
        print 'slave is set to:',second_current

    def get_freq(self):
        # get freq
        fsmodel = self.supervisormodel
        minfreq = fsmodel.get_center_freq() - fsmodel.get_sample_rate() / 2.0
        maxfreq = fsmodel.get_center_freq() + fsmodel.get_sample_rate() / 2.0
        # step = fsmodel.get_sample_rate() / 1021.0
        step = fsmodel.get_sample_rate() / ((config.first - 1) * 10 / 10.0)

        freqs = []
        for j in range(config.first):
            freqs.append(minfreq + j * step)
        return freqs

    def get_up_vol_supervisor(self):
        v_min_supervisor = config.v_min_supervisor
        v_max_supervisor = config.v_max_supervisor
        scan_steps = config.scan_steps

        up_scan_supervisor = np.linspace(v_min_supervisor, v_max_supervisor, scan_steps)
        return up_scan_supervisor

    # use for the x axis when doing moving average
    def get_modified_supervisor_up_current(self):
        aver_point = config.aver_point
        scan_steps = config.scan_steps
        modified_up_vol = self.get_up_vol_supervisor()[(aver_point - 1) / 2:scan_steps - (aver_point - 1) / 2]

        return modified_up_vol

    def get_up_vol_slave(self):
        v_min_slave = config.v_min_slave
        v_max_slave = config.v_max_slave
        scan_steps = config.scan_steps

        up_scan_slave = np.linspace(v_min_slave, v_max_slave, scan_steps)

        return up_scan_slave

    def get_modified_slave_up_current(self):
        aver_point = config.aver_point
        scan_steps = config.scan_steps
        modified_up_vol = self.get_up_vol_slave()[(aver_point - 1) / 2:scan_steps - (aver_point - 1) / 2]
        return modified_up_vol


    # self is fsmodel.get_data(), 1-d ndarray
    def linearize(self,dbm):
        data = []
        for i in range(len(dbm)):
            data.append(10 ** (dbm[i] / 20.0))
        return data

    def get_signal_integration(self,data):
        freq = self.get_freq()
        integral_ref = 0
        # integral width
        width = freq[1] - freq[0]

        # get height, taking first 200 points to get min
        min = 0
        # change min as integral_ref
        for i in range(100):
            min += data[i] / 100.0

        max = data[config.first / 2 - 50]
        max_index = config.first / 2 - 50
        for i in range(config.first / 2 - 50, config.first / 2 + 50, 1):
            if (data[i] > max):
                max = data[i]
                max_index = i

        # halfmax=(max-min)*condition+min
        halfmax = max / (10 ** 0.5) + min
        startpoint = max_index
        while (data[startpoint] - halfmax) > 0:
            startpoint += 1
        rightpoint = startpoint

        startpoint = max_index
        while (data[startpoint] - halfmax) > 0:
            startpoint -= 1
        leftpoint = startpoint

        signal = 0
        for i in range(leftpoint, rightpoint+1, 1):
            signal += (data[i] - integral_ref) * width

        return signal

    def get_moving_ave(self,signal_integration):
        aver_point = config.aver_point
        up_aver_signal = []
        for i in range(len(signal_integration) - aver_point + 1):
            up_aver = 0
            for j in range(aver_point):
                up_aver += signal_integration[i + j] / aver_point
            up_aver_signal.append(up_aver)

        return up_aver_signal

    def get_supervisor_locking_point(self,signal_integration):  # pure signal integration
        aver_line = self.get_moving_ave(signal_integration)
        modified_up_vol = self.get_modified_supervisor_up_current()

        # find max point
        maxium = 0
        max_index = 0
        for i in range(len(aver_line)):
            if aver_line[i] > maxium:
                maxium = aver_line[i]
                max_index = i
            continue

        # set cutting condition
        # print max
        condition = maxium * 0.9
        # find two edge
        right_point = len(modified_up_vol) - 1
        left_point = 0
        for k in range(max_index, len(aver_line), 1):
            if aver_line[k] < condition:
                right_point = k - 1
                break

        for k in range(max_index, 0, -1):
            if aver_line[k] < condition:
                left_point = k + 1
                break

        setting_point = (modified_up_vol[left_point] + modified_up_vol[right_point]) / 2.0
        print 'Supervisor max:', modified_up_vol[max_index]
        print 'Supervisor left:', modified_up_vol[left_point]
        print 'Supervisor right:', modified_up_vol[right_point]
        return setting_point

    def get_slave_locking_point(self,signal_integration):  # pure signal integration
        aver_line = self.get_moving_ave(signal_integration)
        modified_up_vol = self.get_modified_slave_up_current()

        # find max point
        maxium = 0
        max_index = 0
        for i in range(len(aver_line)):
            if aver_line[i] > maxium:
                maxium = aver_line[i]
                max_index = i
            continue

        # set cutting condition
        # print max
        condition = maxium * 0.9
        # find two edge
        right_point = len(modified_up_vol) - 1
        left_point = 0
        for k in range(max_index, len(aver_line), 1):
            if aver_line[k] < condition:
                right_point = k - 1
                break

        for k in range(max_index, 0, -1):
            if aver_line[k] < condition:
                left_point = k + 1
                break

        setting_point = (modified_up_vol[left_point] + modified_up_vol[right_point]) / 2.0
        print 'Slave max:', modified_up_vol[max_index]
        print 'Slave left:', modified_up_vol[left_point]
        print 'Slave right:', modified_up_vol[right_point]
        return setting_point

if __name__ == "__main__":
    from labrad import util
    server = InjectionLock_Server()
    util.runServer( server )

