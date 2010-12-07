class ScheduleError(Exception):
    def __init__(self, *args, **kwargs):
        super(ScheduleError, self).__init__(*args, **kwargs)

class Scheduler(object):
    def __init__(self, context, scavenger):
        super(Scheduler, self).__init__()
        self._context = context
        self._scavenger = scavenger
        
    def schedule(self, service, local_cpu_strength, local_network_speed, prefer_remote):
        """
        Abstract schedule method. This is the only method that _must_
        be implemented in all subclasses.
        @type service: ServiceInvokation (or some subclass).
        @param service: The service invokation object contains the service name,
        input, code, and possibly even more information about the service.
        @type local_cpu_strength: float
        @param local_cpu_strength: The nbench rating of the local cpu.
        @type local_network_speed: float
        @param local_network_speed: The speed of the local network interface.
        @type prefer_remote: bool
        @param prefer_remote: If this parameter is True remote execution is preferred
        even though it may be more efficient to perform the service locally.
        """
        raise NotImplementedError()
