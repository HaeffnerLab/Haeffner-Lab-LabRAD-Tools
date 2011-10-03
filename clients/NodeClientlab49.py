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

#keys are possible node servers, values is list of servers that should
#be started on each node server
nodeDict = {'node_lattice_pc':
				['Data Vault', 'Serial Server', 'DC Box', 'HP Server', 'RS Server red', 'PMT server', 'Direct Ethernet', 'Time Resolved Server', 'Agilent Server', 'Compensation Box','RS Server blue'],
			'node_lab_49':
				['Serial Server', 'LaserDAC'],
			'node_paul_s_box':
				['Paul Box']
			}

for node in ['node_lab_49']:
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