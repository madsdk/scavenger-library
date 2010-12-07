class Candidate(object):
    """
    A candidate peer. This class simply wraps a peer object and its
    currently percieved value as a surrogate.
    """
    def __init__(self, value, peer):
        super(Candidate, self).__init__()
        self._value = value
        self._peer = peer

    def __eq__(self, other):
        if type(other) == type(self):
            return cmp(self, other)
        else:
            return False
        
    def __cmp__(self, other):
        if type(other) == type(self):
            return cmp(self._value, other._value)
        else:
            return False
        
    def _get_peer(self):
        return self._peer
    peer = property(_get_peer)
