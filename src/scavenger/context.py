# Copyright (C) 2008, Mads D. Kristensen
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This file contains all classes that pertain to the context that 
the scavenger client is moving within."""

from __future__ import with_statement
from presence import Presence
import struct
from time import time
from copy import deepcopy
from thread import allocate_lock

class ScavengerPeer(object):
    def __init__(self, name, address, cpu_strength, cpu_cores, active_tasks, network_media):
        """
        Constructor.
        @type name: str
        @param name: The Presence name of the peer offering the scavenger service.
        @type address: ( str, int ) - tuple
        @param address: The RPC address of the peer.
        @type cpu_strength: float
        @param cpu_strength: The CPU performance of the peer.
        @type cpu_cores: int
        @param cpu_cores: The number of cores/CPUs available for use in the peer.
        @type active_tasks: int
        @param active_tasks: The number of tasks actively being worked on by the 
        peer. This may be used as a utilization measurement for the peer.
        @type network_media: str
        @param network_media: The kind of media we can connect to this Peer with.
        """
        super(ScavengerPeer, self).__init__()
        self.name = name.strip()
        self.address = address
        self.cpu_strength = cpu_strength
        self.cpu_cores = cpu_cores
        self.active_tasks = active_tasks
        self.timestamp = time()
        self.net = network_media

    def __eq__(self, other):
        if type(other) == type(self):
            return cmp(self, other)
        else:
            return False

    def __cmp__(self, other):
        # Orders peer items by performance.
        if type(other) == type(self):
            return cmp(self.cpu_strength, other.cpu_strength)
        else:
            return False
        
    def __str__(self):
        return '%s, %s:%i, %f (%f, %i, %i) %i'%(self.name, 
                                            self.address[0], 
                                            self.address[1], 
                                            self.timestamp, 
                                            self.cpu_strength,
                                            self.cpu_cores,
                                            self.active_tasks,
                                            self.net)
        
class Context(object):
    TIMEOUT = 5.0
    CLEANUP_AT = 100
    
    def __init__(self):
        super(Context, self).__init__()
        self.__peers = {}
        self._lock = allocate_lock()

    def add(self, peer):
        with self._lock:
            # Add the peer.
            self.__peers[peer.name] = peer
            
            # Check whether it is time to do some cleaning.
            if len(self.__peers) > Context.CLEANUP_AT:
                now = time()
                for peer in self.__peers.values():
                    if now - peer.timestamp > Context.TIMEOUT:
                        self.__peers.pop(peer.name)
    
    def get_peer(self, name):
        with self._lock:
            return self.__peers[name]
                
    def get_peers(self):
        now = time()
        peers = []
        with self._lock:
            for peer in self.__peers.values():
                # Cleanout stale entries.
                if now - peer.timestamp > Context.TIMEOUT:
                    self.__peers.pop(peer.name)
                else:
                    peers.append(deepcopy(peer))
        return peers
    
    def has_peer(self, name):
        with self._lock:
            return self.__peers.has_key(name)

    def resolve(self, name):
        with self._lock:
            return self.__peers[name].address

    def increment_peer_activity(self, name):
        with self._lock:
            if self.__peers.has_key(name):
                self.__peers[name].active_tasks += 1
        
    def decrement_peer_activity(self, name):
        with self._lock:
            if self.__peers.has_key(name):
                self.__peers[name].active_tasks -= 1
                # Small sanity check here.
                if self.__peers[name].active_tasks < 0:
                    self.__peers[name].active_tasks = 0

class ContextMonitor(object):
    def __init__(self, presence = None):
        super(ContextMonitor, self).__init__()

        # Create the local context.
        self._context = Context()
        
        # Subscribe to Presence announcements.
        if presence == None:
            self._presence = Presence()
            self._presence.connect()
        else:
            self._presence = presence
        self._presence.subscribe('scavenger', self.receive_announcement)
        
    def receive_announcement(self, peer_name, peer_address, service):
        peer_name = peer_name.strip('\x00 ')
        cpu_strength, cpu_cores, active_tasks, network_media = struct.unpack("!fIII", service.data)
        peer = ScavengerPeer(peer_name, (peer_address, service.port), 
                             cpu_strength, cpu_cores, active_tasks, network_media)
        self._context.add(peer)
                
    def get_peers(self):
        return self._context.get_peers()
    
    def has_peer(self, name):
        return self._context.has_peer(name)
    
    def increment_peer_activity(self, name):
        self._context.increment_peer_activity(name)

    def decrement_peer_activity(self, name):
        self._context.decrement_peer_activity(name)

    def shutdown(self):
        self._presence.shutdown(True)
