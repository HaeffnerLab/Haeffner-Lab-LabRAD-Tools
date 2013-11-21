from twisted.internet.defer import inlineCallbacks, returnValue

'''
The shared connection object allows multiple asynchronous clients to share a single connection to the manager
Version 1.0
'''

class connection(object):

    def __init__(self):
        self._servers = {}
        self._on_connect = {}
        self._on_disconnect = {}
    
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        yield self.setupListeners()
        returnValue(self)
    
    @inlineCallbacks
    def get_server(self, server_name):
        connected = yield self._confirm_connected(server_name)
        if connected:
            returnValue(self._servers[server_name])
        else:
            raise Exception("Not connected")
        
    @inlineCallbacks
    def add_on_connect(self, server_name, action):
        connected = yield self._confirm_connected(server_name)
        if not connected:
            print '{} Not Available'.format(server_name)
            return
        try:
            self._on_connect[server_name].append(action)
        except KeyError:
            self._on_connect[server_name] = [action]
    
    @inlineCallbacks
    def add_on_disconnect(self, server_name, action):
        connected = yield self._confirm_connected(server_name)
        if not connected:
            print '{} Not Available'.format(server_name)
            return
        try:
            self._on_disconnect[server_name].append(action)
        except KeyError:
            self._on_disconnect[server_name] = [action]
        
    @inlineCallbacks
    def _confirm_connected(self, server_name):
        if not server_name in self._servers:
            try:
                self._servers[server_name] = yield self.cxn[server_name]
            except Exception, e:
                returnValue(False)
        returnValue(True)
        
    @inlineCallbacks
    def setupListeners(self):
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989+1, True)
        yield self.cxn.manager.addListener(listener = self.followServerConnect, source = None, ID = 9898989)
        yield self.cxn.manager.addListener(listener = self.followServerDisconnect, source = None, ID = 9898989+1)
    
    @inlineCallbacks
    def followServerConnect(self, cntx, server_name):
        print 'server connected'
        server_name = server_name[1]
        print server_name
        if server_name in self._servers.keys():
            print '{} Connected'.format(server_name)
            self._servers[server_name] = yield self.cxn[server_name]
            actions = self._on_connect[server_name]
            for action in actions:
                yield action()
    
    @inlineCallbacks
    def followServerDisconnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name in self._servers.keys():
            print '{} Disconnected'.format(server_name)
            self._servers[server_name] = None
            actions = self._on_disconnect[server_name]
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