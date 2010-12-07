class TaskInvokation(object):
    def __init__(self, name, _input = None, code = None, store = False, scheduler = None):
        super(TaskInvokation, self).__init__()
        self._name = name
        self._input = _input
        self._code = code
        self._store = store
        self._scheduler = scheduler
        self._id = None

    def name(): #@NoSelf
        doc = """Property for name."""
        def fget(self):
            return self._name
        def fset(self, value):
            self._name = value
        def fdel(self):
            del self._name
        return locals()
    name = property(**name())
    
    def input(): #@NoSelf
        doc = """Property for input."""
        def fget(self):
            return self._input
        def fset(self, value):
            self._input = value
        def fdel(self):
            del self._input
        return locals()
    input = property(**input())
    
    def code(): #@NoSelf
        doc = """Property for code."""
        def fget(self):
            return self._code
        def fset(self, value):
            self._code = value
        def fdel(self):
            del self._code
        return locals()
    code = property(**code())

    def store(): #@NoSelf
        doc = """Property for store."""
        def fget(self):
            return self._store
        def fset(self, value):
            self._store = value
        def fdel(self):
            del self._store
        return locals()
    store = property(**store())

    def scheduler(): #@NoSelf
        doc = """Property for scheduler."""
        def fget(self):
            return self._scheduler
        def fset(self, value):
            self._scheduler = value
        def fdel(self):
            del self._scheduler
        return locals()
    scheduler = property(**scheduler())
    
    def id(): #@NoSelf
        doc = """Property for id."""
        def fget(self):
            return self._id
        def fset(self, value):
            self._id = value
        def fdel(self):
            del self._id
        return locals()
    id = property(**id())


class AdaptiveProfTaskInvokation(TaskInvokation):
    def __init__(self, name, _input = None, code = None, store = False, scheduler = 'aprofile',
                 output_size = None, complexity_relation = None):
        super(AdaptiveProfTaskInvokation, self).__init__(name, _input, code, store, scheduler)
        self._output_size = output_size
        self._complexity_relation = complexity_relation
        self._complexity = None

    def output_size(): #@NoSelf
        doc = """Property for output_size"""
        def fget(self):
            return self._output_size
        def fset(self, value):
            self._output_size = value
        def fdel(self):
            del self._output_size
        return locals()
    output_size = property(**output_size())

    def complexity_relation(): #@NoSelf
        doc = """Property for complexity_relation"""
        def fget(self):
            return self._complexity_relation
        def fset(self, value):
            self._complexity_relation = value
        def fdel(self):
            del self._complexity_relation
        return locals()
    complexity_relation = property(**complexity_relation())

    def complexity(): #@NoSelf
        doc = """property for complexity"""
        def fget(self):
            return self._complexity
        def fset(self, value):
            self._complexity = value
        def fdel(self):
            del self._complexity
        return locals()
    complexity = property(**complexity())
    
    