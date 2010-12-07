from service import AdaptiveProfServiceInvokation
from scavenger import Scavenger
from inspect import getsource, getmodule
from functools import partial
import re
import hashlib

# This is a decorator decorator, i.e., a decorator that is used to decorate
# other decoraters. This is done so that the decorated decorator may accept
# parameters; which is not possible otherwise.
def decorator_with_args(decorator):
    def new(*args, **kwargs):
        def new2(fn):
            return decorator(fn, *args, **kwargs)
        return new2
    return new

# This decorator is used when invoking the Adaptive Profiling Scheduler.
@decorator_with_args
def scavenge(fn, output_size, complexity_relation = None, store = False):
    # Modify the source to remove the decorator and rename the method
    # to 'perform'.
    source = getsource(fn)
    source = source[source.find('def'):]
    source = re.sub(r'def\s+([a-zA-Z_][a-zA-Z_0-9]*)', r'def perform', source, 1)

    # Find a suitable name for the task.
    module_name = re.sub(r'[\._]', r'', getmodule(fn).__name__)
    source_md5 = hashlib.md5(source).hexdigest()
    task_name = 'auto.%s.%s'%(module_name, source_md5) 

    # Build a service invokation object.
    service_invokation = AdaptiveProfServiceInvokation(name = task_name, 
                                                       code = source, 
                                                       store = store,
                                                       output_size = output_size,
                                                       complexity_relation = complexity_relation)

    return partial(Scavenger.scavenge_partial, service_invokation, fn)

