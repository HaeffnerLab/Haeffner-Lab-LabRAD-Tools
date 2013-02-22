import labrad

nodeDict = {'node_lab_49':
                    ['Pulser_729'],
        }
#connect to LabRAD
errors = False
try:
    cxn = labrad.connect('192.168.169.49')
except:
    print 'Please start LabRAD Manager'
    errors = True
else:
    for node in nodeDict.keys():
        #make sure all node servers are up
        if not node in cxn.servers:'{} is not running'.format(node)
        else:
            print '\nWorking on {} \n '.format(node)
            cxn.servers[node].refresh_servers()
            #if node server is up, start all possible servers on it that are not already running
            running_servers = cxn.servers[node].running_servers().asarray
            for server in nodeDict[node]:
                if server not in running_servers: 
                    print server + ' is not running'
                else:
                    print 'restarting ' + server
                    try:
                        cxn.servers[node].stop(server)
                        cxn.servers[node].start(server)
                    except Exception as e:
                        print 'ERROR with ' + server
                        errors = True