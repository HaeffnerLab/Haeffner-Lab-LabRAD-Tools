from labrad.types import Error

class dds_access_locked(Error):
    
    def __init__(self):
        super(dds_access_locked, self).__init__(
            msg = 'DDS Access Locked: running a pulse sequence',
            code = 1
            )