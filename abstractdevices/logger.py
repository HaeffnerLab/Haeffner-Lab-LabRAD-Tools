"""
### BEGIN NODE INFO
[info]
name = Logger
version = 1.0
description = 
instancename = Logger

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, Signal, setting
from twisted.internet.defer import inlineCallbacks, returnValue
from datetime import datetime

class Logger( LabradServer ):
    """Helps with logging of messages from servers and clients"""

    name = 'Logger'
    keepLastMessages = 1000
    onNewLog = Signal(223423, 'signal: new entry', '(tss)')
    
#     @inlineCallbacks
    def initServer( self ):
        self.listeners = set()
        self.unseen_count = {}
        self.logged_messages = []
        
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
        self.unseen_count[c.ID] = len(self.logged_messages)

    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
    @setting(1, 'Add Log', log=['ss'], returns=['wtss'])
    def add_log(self, c, log):
        """Adds a lot. The input should be in the form (sender name, message)"""
        priority,sender_name,message = log
        if not 0 <= priority <= 2:
            raise Exception("Priority should be between 0 and 2")
        combined = (datetime.now(),priority,sender_name,message)
        self.logged_messages.append(combined)
        if len(self.logged_messages) > self.keepLastMessages:
            self.logged_messages.pop(0)
        for context in self.unseen_count.keys():
            self.unseen_count[context] += 1
        return combined
    
    @setting(2, "Get Log", how_many_lines = 'w',  returns=['*(wtss)'])
    def get_log(self, c, how_many_lines = None):
        """Gets the log. Can specifiy how many lines to retrieve, counting from last. If not specified will get all the entire log"""
        if how_many_lines is None:
            how_many_lines = self.keepLastMessages
        #this indexing is safe in case how_many_lines is too large
        print max(0, self.unseen_count[c.ID] - how_many_lines)
        self.unseen_count[c.ID] = max(0, self.unseen_count[c.ID] - how_many_lines)
        return self.logged_messages[-how_many_lines:]
    
    @setting(3, "Get New Log", returns=['*(wtss)'])
    def get_new_log(self, c):
        """Returns only logs unseen in the context"""
        how_many_lines = self.unseen_count[c.ID]
        if how_many_lines == 0:
            return []
        else:
            self.unseen_count[c.ID] = 0
        return self.logged_messages[-how_many_lines:]
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(Logger())