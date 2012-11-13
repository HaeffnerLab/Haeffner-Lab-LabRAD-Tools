from twisted.internet.defer import inlineCallbacks, returnValue

class connection(object):
    
    servers = {
                'Data Vault':None,
                'Semaphore':None
                }
    
    def __init__(self):
        self.on_connect = {}.fromkeys(self.servers)
        self.on_disconnect = {}.fromkeys(self.servers)
        #initialize these to empty lists
        for key in self.on_connect:
            self.on_connect[key] = []
        for key in self.on_disconnect:
            self.on_disconnect[key] = []
    
    @inlineCallbacks
    def connect(self):
        print 'Connecting'
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        for server_name in self.servers.keys():
            try:
                self.servers[server_name] = yield self.cxn[server_name]
            except Exception, e:
                print '{} Not Available'.format(e)
        yield self.setupListeners()
        print 'Connected'
        returnValue(self)
            
    @inlineCallbacks
    def setupListeners(self):
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989+1, True)
        yield self.cxn.manager.addListener(listener = self.followServerConnect, source = None, ID = 9898989)
        yield self.cxn.manager.addListener(listener = self.followServerDisconnect, source = None, ID = 9898989+1)
    
    @inlineCallbacks
    def followServerConnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name in self.servers.keys():
            print '{} Connected'.format(server_name)
            self.servers[server_name] = yield self.cxn[server_name]
            actions = self.on_connect[server_name]
            for action in actions:
                yield action()
    
    @inlineCallbacks
    def followServerDisconnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name in self.servers.keys():
            print '{} Disconnected'.format(server_name)
            self.servers[server_name] = None
            actions = self.on_disconnect[server_name]
            for action in actions:
                yield action()
    
    @inlineCallbacks
    def context(self):
        cntx = yield self.cxn.context()
        returnValue(cntx)
            
if __name__ == '__main__':
    from twisted.internet import reactor
    app = connection()
    reactor.callWhenRunning(app.connect)
    reactor.run()