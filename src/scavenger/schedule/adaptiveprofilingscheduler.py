"""
This is the adaptive profiling scheduler that adapts its scheduling information
to the user defined expression given in the decorator. The developer may thus
designate that running time varies with the size or value of one or more inputs.
"""

from __future__ import with_statement
from scheduler import Scheduler, ScheduleError
from scrpc import SCProxy
from cPickle import dumps
from datastore import RemoteDataHandle
import re
from profile_common import Profile
from common import Candidate
from threading import Lock
    
class AdaptiveProfScheduler(Scheduler):
    def __init__(self, context, scavenger):
        super(AdaptiveProfScheduler, self).__init__(context, scavenger)
        self._lprofile = Profile(filename='alprofile.dat')
        self._gprofile = Profile(filename='agprofile.dat')
#        self._log = open('/tmp/scavenger-aprofile.log', 'w')
#        self._log_lock = Lock()
        self._schedule_lock = Lock()
        
    def _get_datahandles(self, task_input):
        datahandles = []
        if type(task_input) == dict:
            # Keyword arguments.
            for item in task_input.values():
                if type(item) == RemoteDataHandle:
                    datahandles.append(item)
        elif type(task_input) in (tuple, list):
            # Positional arguments.
            for item in task_input:
                if type(item) == RemoteDataHandle:
                    datahandles.append(item)
        else:
            # Single argument.
            if type(task_input) == RemoteDataHandle:
                datahandles.append(task_input)

        return datahandles
        
    def _get_lprofile(self):
        return self._lprofile
    lprofile = property(_get_lprofile)

    def _get_gprofile(self):
        return self._gprofile
    gprofile = property(_get_gprofile)

    def schedule(self, task, local_cpu_strength, local_network_speed, local_activity, prefer_remote=False):
        with self._schedule_lock:
            # For profiling use we need to find the size/factor that relates input to task complexity.
            if task.complexity_relation != None:
                if not type(task.input) in (tuple, list):
                    raise Exception('This only works on tasks with list-input for now...') 
                expression = re.sub(r'#(\d+)', r'task.input[\1]', task.complexity_relation)
                try:
                    task.complexity = eval(expression)
                except Exception, e:
                    raise Exception('Error evaluating complexity expression.', e)

            # If no peers are available raise an exception to signal that local
            # execution should be performed.
            peers = self._context.get_peers()
            if len(peers) == 0:
                local_activity.increment()
                # Log where the task will be performed.
#                if task.id != None:
#                    with self._log_lock:
#                        self._log.write("%s -> %s\n"%('localhost', task.id))
                raise ScheduleError('No usable surrogates found.') 

            # Find the input size. 
            input_size = len(dumps(task.input, -1))
            # If task code is given its size must be added to the total input size.
            if task.code != None:
                input_size += len(task.code)

            # Get a list of data handles in the input.
            datahandles = self._get_datahandles(task.input)

            # Find the size of the sevice output.
            if task.store == True:
                # If the output is not fetched we need not consider it here.
                output_size = 0
            else:
                if type(task.output_size) in (int, float):
                    # A constant is given - we simply adopt that number.
                    output_size = task.output_size
                else:
                    # We now assume that task.output_size is a string containing a 
                    # formula relating the output size to the input size.
                    # Note: The DC scheduler only works on tasks with list-input for now...
                    if not type(task.input) in (tuple, list):
                        raise Exception('The scheduler only works on tasks with list-input for now...') 
                    expression = re.sub(r'#(\d+)', r'task.input[\1]', task.output_size)
                    try:
                        output_size = eval(expression)
                    except Exception, e:
                        raise Exception('Error evaluating output complexity expression.', e)
                
            # Create the candidate list.
            candidates = []

            # Get the global complexity.
            global_complexity = self._gprofile.get_complexity(task.name, input_complexity = task.complexity)

            # Start by adding the local peer.
            if not prefer_remote:
                peer_strength = float(local_cpu_strength) / (local_activity.value + 1)
                task_complexity = self._lprofile.get_complexity(('localhost', task.name), global_complexity, task.complexity)
                time_to_perform = task_complexity / peer_strength

                time_to_transfer = 0
                for datahandle in datahandles:
                    bandwidth = min(local_network_speed, self._context.get_peer(datahandle.server_address).net)
                    time_to_transfer += (float(datahandle.size) / bandwidth)

                total_time = time_to_perform + time_to_transfer
                candidates.append(Candidate(total_time, None))

            # Then add remote peers.
            for peer in peers:
                # Find out how long it would take for the peer to perform the task.
                peer_strength = float(peer.cpu_strength)/(peer.active_tasks/peer.cpu_cores+1)
                task_complexity = self._lprofile.get_complexity((peer.name, task.name), global_complexity, task.complexity)
                time_to_perform = task_complexity / peer_strength

                # Find out how long it would take to transfer the input to the peer.
                # 0.1 seconds of latency is added.
                time_to_transfer = float(input_size + output_size) / min(local_network_speed, peer.net) + 0.1 
                for datahandle in datahandles:
                    if datahandle.server_address != peer.name:
                        bandwidth = min(peer.net, self._context.get_peer(datahandle.server_address).net)
                        time_to_transfer += (float(datahandle.size) / bandwidth)

                total_time = time_to_perform + time_to_transfer
                candidates.append(Candidate(total_time, peer))

            # Sort the peers by the time it would take for them to perform the task.
            candidates.sort()

            # Perform the task.
            surrogate = candidates[0].peer

            # Check whether this is local execution.
            if surrogate == None:
                # By raising this exception we force the Scavenger lib to
                # do local execution.
                local_activity.increment()
                # Log where the task will be performed.
#                if task.id != None:
#                    with self._log_lock:
#                        self._log.write("%s -> %s\n"%('localhost', task.id))
                raise ScheduleError('Do local execution.')

            connection = SCProxy(surrogate.address)
            try:
                # Mark that the surrogate is now more busy :)
                self._context.increment_peer_activity(surrogate.name)

                # Release the scheduling lock here. Now others may schedule tasks while 
                # this task is being performed.
                self._schedule_lock.release()
                try:
                    if not self._scavenger.has_task(surrogate, task.name, connection):
                        self._scavenger.install_task(surrogate, task.name, task.code, connection)

                    # Log where the task will be performed.
#                    if task.id != None:
#                        with self._log_lock:
#                            self._log.write("%s -> %s\n"%(surrogate.name, task.id))

                    # And perform the task.
                    result = self._scavenger.perform_scheduled_task(surrogate, task, connection)
                finally:
                    self._schedule_lock.acquire()

                # Decrement the activity count.
                self._context.decrement_peer_activity(surrogate.name)
                return result
            finally:
                try: connection.close() 
                except: pass
