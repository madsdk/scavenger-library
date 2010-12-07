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

"""The client side API needed to work with Scavenger hosts."""

from __future__ import with_statement
from context import ContextMonitor
from scrpc import SCProxy
from schedule import ScheduleError, AdaptiveProfScheduler
from config import Config
from datastore import RemoteDataHandle
from service import ServiceInvokation
from time import time
from threading import Lock
from copy import deepcopy
import os

def shutdown():
    Scavenger.shutdown()

class ScavengerException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class SingletonException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)

class LocalActivity(object):
    def __init__(self):
        super(LocalActivity, self).__init__()
        self._lock = Lock()
        self._value = 0
    def increment(self):
        with self._lock:
            self._value += 1
    def decrement(self):
        with self._lock:
            self._value -= 1
    def _get_value(self):
        with self._lock:
            return self._value
    value = property(_get_value)

class ScavengerDefines(object):
    TIMEOUT = 600
    
class Scavenger(object):
    INSTANCE = None

    @classmethod
    def get_instance(cls):
        if cls.INSTANCE != None:
            return cls.INSTANCE
        else:
            cls()
            if not cls.INSTANCE:
                raise SingletonException('Error creating Scavenger instance.')
            return cls.INSTANCE

    def __init__(self):
        """Constructor."""
        # Do singleton checking.
        if Scavenger.INSTANCE != None:
            raise SingletonException('A Scavenger instance already exists.')

        # Initialize the object.
        super(Scavenger, self).__init__()

        # Create a context monitor.
        self._monitor = ContextMonitor()

        # Create the schedulers.
        self._schedulers = {}
        self._schedulers['aprofile'] = AdaptiveProfScheduler(self._monitor._context, Scavenger)

        # Load in the config.
        self._config = Config.get_instance()

        # Set the local activity count.
        self._activity = LocalActivity()
        
        # Assign the instance pointer.
        Scavenger.INSTANCE = self

    @classmethod
    def get_peers(cls):
        return cls.INSTANCE._get_peers()

    def _get_peers(self):
        """
        Get a list of known peers offering the scavenger service.
        @rtype: list
        @return: A list of ScavengerPeer objects for the peers that are currently available.
        """
        return self._monitor.get_peers()
    
    @classmethod
    def perform_service(cls, peer, service_name, service_input, connection=None, 
                        timeout=ScavengerDefines.TIMEOUT, store=False):
        return cls.INSTANCE._perform_service(peer, service_name, service_input, 
                                             connection, timeout, store)

    def _perform_service(self, peer, service_name, service_input, connection=None, 
                         timeout=ScavengerDefines.TIMEOUT, store=False):
        """
        Try to perform a service at a remote scavenger host.
        @type peer: ScavengerPeer
        @param peer: The peer where the service should be performed.
        @type service_name: str
        @param service_name: The name of the service.
        @type service_input: dict
        @param service_input: The input for the service.
        @type connection: SCProxy
        @param connection: An initiated connection to a Scavenger peer.
        @type timeout: float
        @param timeout: The number of seconds to wait for the result before 
        quitting.
        @type store: bool
        @param store: Whether or not the surrogate should store the result locally.
        @raise ScavengerException: If the surrogate can not be contacted, or if
        an error occurs during remote execution.
        """
        print peer.name, #DEBUG

        # Check that the peer is still there.
        if not self._monitor.has_peer(peer.name):
            raise ScavengerException('No such peer is within range.')
        
        # Fire the RPC call.
        proxy = connection if connection != None else SCProxy(peer.address)
        try:
            return proxy.perform_task(service_name, service_input, timeout, store)
        finally:
            if connection == None:
                proxy.close()
    

    @classmethod
    def perform_scheduled_service(cls, peer, service, connection = None):
        return cls.INSTANCE._perform_scheduled_service(peer, service, connection)

    def _perform_scheduled_service(self, peer, service, connection):
        print peer.name, #DEBUG

        # Check that the peer is still there.
        if not self._monitor.has_peer(peer.name):
            raise ScavengerException('No such peer is within range.')
        
        # Fire the RPC call.
        proxy = connection if connection != None else SCProxy(peer.address)
        try:
            if service.scheduler in ('aprofile'):
                result, complexity = proxy.perform_task(service.name, service.input, ScavengerDefines.TIMEOUT, service.store, True)
                if service.scheduler == 'aprofile':
                    self._schedulers[service.scheduler].gprofile.register(service.name, complexity, service.complexity)
                    self._schedulers[service.scheduler].lprofile.register((peer.name, service.name), complexity, service.complexity)
                return result
            else:
                return proxy.perform_task(service.name, service.input, ScavengerDefines.TIMEOUT, service.store, False)
        finally:
            if connection == None:
                proxy.close()


    @classmethod
    def install_service(cls, peer, service_name, service_code, connection=None):
        cls.INSTANCE._install_service(peer, service_name, service_code, connection)

    def _install_service(self, peer, service_name, service_code, connection=None):
        """
        Installs the given service onto the given peer.
        @type peer: ScavengerPeer
        @param peer: The peer where the service is to be installed.
        @type service_name: str
        @param service_name: The name of the new service. This must be on 
        the form name1.name2.name3, e.g., 'daimi.imaging.scale'.
        @type service_code: str
        @param service_code: The source code of the service.
        @type connection: SCProxy
        @param connection: An initiated connection to a Scavenger peer.
        @raise ScavengerException: If the peer cannot be contacted, or if an 
        error occurs at the remote peer during installation. 
        """
        # Check that the peer is still there.
        if not self._monitor.has_peer(peer.name):
            raise ScavengerException('No such peer is within range.')
        
        # Fire the RPC call.
        proxy = connection if connection != None else SCProxy(peer.address)
        try:
            proxy.install_task(service_name, service_code)
        finally:
            if connection == None:
                proxy.close()

    @classmethod
    def has_service(cls, peer, service_name, connection=None):
        return cls.INSTANCE._has_service(peer, service_name, connection)

    def _has_service(self, peer, service_name, connection=None):
        """
        Checks whether the given peer offers the named service.
        @type peer: ScavengerPeer
        @param peer: The peer that is to be checked.
        @type service_name: str
        @param service_name: The name of the service.
        @type connection: SCProxy
        @param connection: An initiated connection to a Scavenger peer.
        @raise ScavengerException: If the peer can not be contacted, or if
        an error occurs at the remote peer.
        """
        # Check that the peer is still there.
        if not self._monitor.has_peer(peer.name):
            raise ScavengerException('No such peer is within range.')
        
        # Fire the RPC call.
        proxy = connection if connection != None else SCProxy(peer.address)
        try:
            return proxy.has_task(service_name)
        finally:
            if connection == None:
                proxy.close()
    
    def _resolve_data_handles(self, service_input):
        """Resolves any remote data handles in the input so that 
        local execution may be performed."""
        if type(service_input) == dict:
            for key, value in service_input.items():
                if type(value) == RemoteDataHandle:
                    service_input[key] = Scavenger.fetch_data(value)
        elif type(service_input) in (tuple, list):
            new_service_input = []
            for item in service_input:
                if type(item) == RemoteDataHandle:
                    new_service_input.append(Scavenger.fetch_data(item))
                else:
                    new_service_input.append(item)
            service_input = new_service_input
        else:
            if type(service_input) == RemoteDataHandle:
                service_input = Scavenger.fetch_data(service_input)
        return service_input

    @classmethod
    def scavenge(cls, service_name, service_input, service_code=None, local_code=None):
        service_invocation = ServiceInvokation(service_name, service_input, service_code) 
        return cls.INSTANCE._scavenge(service_invocation, local_code)
    
    def _scavenge(self, service, local_code=None):
        """
        This method offers opportunistic use of nearby computing resources.
        The process works in the following way:
        1) If surrogates are available we check to see if any of them have the
           service in question. If so we forward the task of performing the 
           service to such a peer.
        2) If no peers were found in step 1 a random surrogate is chosen
           (if any are available), the service is installed at that surrogate, 
           and the service is performed. 
        3) If no surrogates are available at all the function given in the 
           local_code argument is invoked with the service input. 
        @type service: ServiceInvokation
        @param service: The service that must be invoked. This object
        contains the service name, input, code and possible more information about
        the service.
        @type local_code: function
        @param local_code: A local function that is capable of performing the 
        service. This may be the same code that is used when performing the service
        remotely, or it may be a 'lighter' version of the code that yields a lower
        quality result but is better suited for executing on a small device. 
        @rtype: Depends on the service being performed.
        @return: The result of performing the service.
        @raise ScavengerException: For lots of reasons...
        """
        # Schedule the service execution.
        try:
            # Ask the scheduler to schedule the task.
            if local_code == None:
                # If we do not have local code we need to enable prefer_remote.
                return self._schedulers[service.scheduler].schedule(service,
                                                                    self._config.getfloat('cpu', 'strength'), 
                                                                    self._config.getint('network', 'speed'), 
                                                                    self._activity, 
                                                                    True)
            else:
                return self._schedulers[service.scheduler].schedule(service, 
                                                                    self._config.getfloat('cpu', 'strength'),
                                                                    self._config.getint('network', 'speed'),
                                                                    self._activity)
        except ScheduleError:
            # Remote execution was not possible. Do local execution if possible.
            if local_code != None:
                print 'localhost', #DEBUG

                # Resolve any remote data handles.
                service.input = self._resolve_data_handles(service.input)

                def perform_local_function(service_input):
                    try:
                        # Perform the local function.
                        if type(service_input) == dict:
                            return local_code(**service_input)
                        elif type(service_input) in (tuple, list):
                            return local_code(*service_input)
                        else:
                            return local_code(service_input)
                    finally:
                        self._activity.decrement()

                
                if service.scheduler in ('aprofile'):
                    # We need to profile this service run.
                    start = time()
                    start_activity = self._activity.value
                    result = perform_local_function(service.input)
                    stop_activity = self._activity.value + 1
                    stop = time()
                    activity_level = float(start_activity + stop_activity) / 2
                    complexity = ((stop-start) * self._config.getfloat('cpu', 'strength')) / activity_level
                    if service.scheduler == 'aprofile':
                        self._schedulers[service.scheduler].gprofile.register(service.name, complexity, service.complexity)
                        self._schedulers[service.scheduler].lprofile.register(('localhost', service.name), complexity, service.complexity)
                    return result
                else:
                    return perform_local_function(service.input)
                    
            else:
                raise ScavengerException('No surrogates available.')
         
    @classmethod
    def scavenge_partial(cls, service_invokation, local_function, *service_input, **kwargs):
        invocation = deepcopy(service_invokation)
        invocation.input = service_input
        if kwargs.has_key('id'):
            invocation.id = kwargs['id']
        return cls.INSTANCE._scavenge(invocation, local_function)

    @classmethod
    def shutdown(cls):
        cls.INSTANCE._shutdown()

    def _shutdown(self):
        """Make a clean break from Presence."""
        self._monitor.shutdown()
        # Save the profiling data.
        self._schedulers['aprofile'].lprofile.save()
        self._schedulers['aprofile'].gprofile.save()
#        self._schedulers['aprofile']._log.close()

    @classmethod
    def resolve(cls, peer_name):
        """Recolves a peer name (presence id) to an ip,port tuple."""
        return cls.INSTANCE._monitor._context.resolve(peer_name)

    @classmethod
    def fetch_data(cls, rdh, connection=None):
        return rdh.fetch(connection, cls.INSTANCE._monitor._context)

    @classmethod
    def store_data(cls, peer, data, connection=None):
        # Check that the peer is still there.
        if not cls.INSTANCE._monitor.has_peer(peer.name):
            raise ScavengerException('No such peer is within range.')
        
        # Fire the RPC call.
        proxy = connection if connection != None else SCProxy(peer.address)
        try:
            return proxy.store_data(data)
        finally:
            if connection == None:
                proxy.close()

    @classmethod
    def retain_data(cls, rdh, connection=None):
        rdh.refresh(connection, cls.INSTANCE._monitor._context)

    @classmethod
    def expire_data(cls, rdh, connection=None):
        rdh.expire(connection, cls.INSTANCE._monitor._context)

# Create the initial instance.
Config(os.path.join(os.environ['HOME'], '.scavenger', 'config.ini'))
Scavenger()
