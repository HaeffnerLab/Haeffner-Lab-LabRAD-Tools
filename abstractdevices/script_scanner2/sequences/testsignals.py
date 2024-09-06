# test subscribing to scriptscanner signals
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredLock, Deferred


class test():

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.context = yield self.cxn.context()
        self.sc = yield self.cxn['ScriptScanner']
        yield self.setupListeners()

    @inlineCallbacks
    def setupListeners(self):
        yield self.sc.signal_on_running_script_finished(192934, context=self.context)
        yield self.sc.addListener(listener = self.follow, source = None, ID = 192934, context = self.context)

    def follow(self, x, y):
        print "script finished!"
        print x
        print y

    

if __name__ == '__main__':
    from twisted.internet import reactor
    a = test()
    reactor.callWhenRunning(a.connect)
    reactor.run()
