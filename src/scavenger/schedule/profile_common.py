from __future__ import with_statement
from thread import allocate_lock
from cPickle import load, dump
from math import fabs
import os

def binary_search(l, x):
    """Searches through the sorted list l for the value closest to x."""
    lo = 0
    hi = len(l)
    mid = None
    while lo < hi:
        mid = (lo+hi)/2
        if x > l[mid]:
            # Go right (up).
            lo = mid+1
        elif x < l[mid]:
            # Go left (down).
            hi = mid
        else:
            return mid
    return mid

def sandwish(l, x):
    """Returns the two positions that x lies between w.r.t. value in the sorted list l.
    I.e., it returns the place where x could be inserted to maintain the ordering."""
    pos = binary_search(l, x)
    if pos == None:
        return None
    else:
        if l[pos] == x:
            return (pos, pos)
        elif l[pos] < x:
            if len(l) > pos+1:
                return (pos, pos+1)
            else:
                return (pos, pos)
        else:
            if pos > 0:
                return (pos-1, pos)
            else:
                return (pos, pos)

def closest_to_me(l, x):
    yz = sandwish(l, x)
    if yz == None:
        return None
    else:
        y, z = yz
        if y == z:
            return y
        else:
            diff_to_y = x - l[y]._key
            diff_to_z = l[z]._key - x
            if diff_to_y <= diff_to_z:
                return y
            else:
                return z

class ProfileBucket(object):
    def __init__(self, key, backlog_size):
        super(ProfileBucket, self).__init__()
        self._key = key
        self._backlog_size = backlog_size
        self._backlog = []

    def __cmp__(self, other):
        if type(other) == type(self):
            return cmp(self._key, other._key)
        else:
            return cmp(self._key, other)

    def register(self, value):
        # Prune out old entries if necessary.
        if len(self._backlog) >= self._backlog_size:
            self._backlog.pop(0)
        # Add the new entry.
        self._backlog.append(value)

    def get_complexity(self):
        return reduce(lambda x, y: x + y, self._backlog) / len(self._backlog)
        

class ProfileItem(object):
    DEFAULT_COMPLEXITY = 0.0
    COMPLEXITY_VARIATION = 0.2 # The complexity has to vary at least this much before we create a new bucket.
    SIZE_VARIATION = 0.01 # The input size has to vary at least this much before we create a new bucket.

    def __init__(self, backlog_size):
        super(ProfileItem, self).__init__()
        self._backlog_size = backlog_size
        self._backlog = []

    def register(self, value, input_size = None):
        if input_size != None:
            # This is a two-dimensional profile item.
            # When registering we first look for the bucket with the values closest to
            # this new value.
            candidate_position = closest_to_me(self._backlog, input_size)
            if candidate_position == None:
#                print 'new bucket!!'
                # There is nothing in the list.
                # We must create a new bucket for this item.
                new_bucket = ProfileBucket(input_size, self._backlog_size)
                new_bucket.register(value)
                self._backlog.insert(0, new_bucket)
            else:
                # We have found a candidate. Now continue to figure out where this item
                # belongs.
                candidate = self._backlog[candidate_position]
                # Check how much that bucket's complexity value varies from this new one.
                candidate_complexity = candidate.get_complexity()
                complexity_variation = fabs((candidate_complexity - value) / candidate_complexity)
                input_size_variation = fabs((float(candidate._key - input_size)) / candidate._key)
#                print 'variations', complexity_variation, input_size_variation #DEBUG
                if complexity_variation > ProfileItem.COMPLEXITY_VARIATION and input_size_variation > ProfileItem.SIZE_VARIATION:
#                    print 'new bucket!' #DEBUG
                    # We must create a new bucket for this item.
                    new_bucket = ProfileBucket(input_size, self._backlog_size)
                    new_bucket.register(value)
                    if candidate > new_bucket:
                        self._backlog.insert(candidate_position, new_bucket)
                    else:
                        self._backlog.insert(candidate_position + 1, new_bucket)
                else:
                    # The item fits inside this bucket.
                    candidate.register(value)
        else:
            # This is a standard, single-dimensional profile item.
            # Prune out old entries if necessary.
            if len(self._backlog) >= self._backlog_size:
                self._backlog.pop(0)
            # Add the new entry.
            self._backlog.append(value)

    def get_complexity(self, input_size = None):
        if input_size != None:
            # This is a two-dimensional thingy.
            candidate_position = closest_to_me(self._backlog, input_size)
            if candidate_position == None:
                # The backlog is empty.
                return ProfileItem.DEFAULT_COMPLEXITY
            else:
                return self._backlog[candidate_position].get_complexity()
        else:
            # This is the regular single-dimensional backlog.
            # if no measurements are available we return the default.
            if len(self._backlog) == 0:
                return ProfileItem.DEFAULT_COMPLEXITY
            # Otherwise we return the average of the backlog. 
            # TODO: This could be varied to put more or less weight to new vs. old information.
            return reduce(lambda x, y: x + y, self._backlog) / len(self._backlog)

class Profile(object):
    def __init__(self, backlog = 10, filename = 'profile.dat'):
        super(Profile, self).__init__()
        self._backlog = backlog
        self._filename = os.path.join(os.environ['HOME'], '.scavenger', filename)
        self._data = {}
        self._lock = allocate_lock()

        # Try to load in profile data.
        if os.path.exists(self._filename):
            with open(self._filename, 'rb') as infile:
                self._data = load(infile)
            if type(self._data) != dict:
                # Silently ignore this for now - later on logging should be used.
                self._data = {}
        
    def register(self, key, value, input_complexity = None):
        with self._lock:
            # Make sure that an entry for that key exists.
            if not self._data.has_key(key):
                self._data[key] = ProfileItem(self._backlog)
        
            # Add the measurement.
            self._data[key].register(value, input_complexity)
        
    def get_complexity(self, key, default = ProfileItem.DEFAULT_COMPLEXITY, input_complexity = None):
        with self._lock:
            # Check whether an item for this service exists.
            if not self._data.has_key(key):
                return default
            # We have run this service before - return the expected complexity.
            return self._data[key].get_complexity(input_complexity)

    def save(self):
        with self._lock:
            with open(self._filename, 'wb') as outfile:
                dump(self._data, outfile, -1)
