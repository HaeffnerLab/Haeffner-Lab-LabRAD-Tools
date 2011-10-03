import labrad
import numpy as np
import time

#connect to LabRAD
try:
	cxn = labrad.connect()
except:
	print 'Please start LabRAD Manager'
	time.sleep(10)
	raise()

nodeDict = {'node_lattice_pc':
				['Data Vault', 'Serial Server', 'DC Box', 'HP Server', 'Compensation Box','NormalPMTCountFPGA',
				'Agilent Server', 'GPIB Bus','GPIB Device Manager', 'RohdeSchwarz Server','Tektronix Server','Trigger','NormalPMTFlow','Double Pass',
				'Compensation LineScan'],
			'node_lab_49':
				['Serial Server', 'LaserDAC'],
			'node_lab_197':
				['Paul Box','dataProcessor','TimeResolvedFPGA']
			}

for node in ['node_lab_197','node_lab_49','node_lattice_pc']: #sets the order of opening
	#make sure all node servers are up
	if not node in cxn.servers: print node + ' is not running'
	else:
		print '\n' + 'Working on ' + node + '\n'
		#if node server is up, start all possible servers on it that are not already running
		running_servers = np.array(cxn.servers[node].running_servers().asarray)
		for server in nodeDict[node]:
			if server in running_servers: 
				print server + ' is already running'
			else:
				print 'starting ' + server
				try:
					cxn.servers[node].start(server)
				except:
					print 'ERROR with ' + server
					
time.sleep(10)