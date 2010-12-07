from __future__ import with_statement
from ConfigParser import SafeConfigParser
import os
from time import time, sleep
from threading import Thread
from thread import allocate_lock

class Config(SafeConfigParser):
    INSTANCE = None

    @classmethod
    def get_instance(cls):
        if cls.INSTANCE == None:
            cls.INSTANCE = cls()
        return cls.INSTANCE
    
    def __init__(self, filename):
        # Do singleton checking.
        if Config.INSTANCE != None:
            raise Exception('Singleton error: an instance of Config already exists.')
        
        # Create the parent dir if it does not exist.
        if not os.path.exists(filename):
            dirname = os.path.dirname(filename) 
            if dirname != '':
                os.mkdir(dirname)

        # Initialize the config by reading in the file and then checking if 
        # standard values must be plugged in...
        SafeConfigParser.__init__(self)
        self._filename = filename
        self.read(self._filename)
        self._dirty = False
        self.set_defaults()
        
        # Write the config file if necessary.
        if self._dirty:
            with open(self._filename, 'wb') as configfile:
                self.write(configfile)
                self._dirty = False

        # Set the singleton pointer.
        Config.INSTANCE = self
    
    def add_section(self, section):
        self._dirty = True
        return SafeConfigParser.add_section(self, section)
    
    def set(self, section, option, value):
        self._dirty = True
        return SafeConfigParser.set(self, section, option, value)

    # These media speeds are teoretical speed in bytes/sec * 0.75. 
    # For the wireless media types this is divided by two, which seems
    # to be the actual transfer speeds obtained using these media.
    MEDIA = {
        'BT-1'   : '34000',
        'BT-2'   : '100000',
        'WLAN-b' : '500000', 
        'LAN10'  : '937500',
        'WLAN-g' : '2500000',
        'LAN100' : '9375000', 
        'LAN1K'  : '93750000',
        }

    def set_defaults(self):
        # Network information.
        if not self.has_section('network'):
            self.add_section('network')
        if not self.has_option('network', 'speed'):
            self.set('network', 'speed', '500000')
        else:
            # If the option is there we check whether we should
            # translate it into an integer here.
            if self.get('network', 'speed') in Config.MEDIA.keys():
                self.set('network', 'speed', 
                         Config.MEDIA[self.get('network', 'speed')])
        
        # CPU information.
        if not self.has_section('cpu'):
            self.add_section('cpu')
        if not self.has_option('cpu', 'strength'):
            measurer = BogomipsMeasurer()
            measurer.start()
            int_perf, float_perf = measurer.measure(1.0)
            measurer.shutdown()
            del measurer
            self.set('cpu', 'strength', str((((float_perf + int_perf) / 2.0)) / 25000))
        if not self.has_option('cpu', 'cores'):
            self.set('cpu', 'cores', '1')

class BogomipsMeasurer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_thread = False
        self.start_measurement = False
        self.stop_measurement = False
        self.int_measure = 0.0
        self.float_measure = 0.0
        self.daemon = True
        self.signal = allocate_lock()
        self.signal.acquire()
        
    def run(self):
        # Wait for someone to tell you to start.
        while not self.stop_thread:
            while not self.start_measurement:
                if self.stop_thread:
                    return 0
                sleep(0.01)
        
            # Measure integer performance. 
            start_int = time()
            i = 0
            x = 0
            while not self.stop_measurement:
                x += 42
                x /= 7
                x *= 6
                x -= 36
                i += 1
            stop_int = time()
            if self.stop_thread:
                return 0
            try:
                self.int_measure = float(i)/(stop_int-start_int)
            except:
                self.int_measure = 0.0
                
            # Measure float performance.
            self.stop_measurement = False
            start_float = time()
            i = 0
            x = 0.0
            while not self.stop_measurement:
                x += 49.7
                x /= 7.1
                x *= 6.9
                x -= 48.3
                i += 1
            stop_float = time()
            if self.stop_thread:
                return 0
            try:
                self.float_measure = float(i)/(stop_float-start_float)
            except:
                self.float_measure = 0.0
        
            # Return to being idle.
            self.start_measurement = False
            self.stop_measurement = False
            
            # Signal that data is ready.
            self.signal.release()
        
    def measure(self, interval=0.10):
        self.start_measurement = True
        sleep(interval)
        self.stop_measurement = True
        sleep(interval)
        self.stop_measurement = True
        self.signal.acquire()
        return (self.int_measure, self.float_measure)
    
    def shutdown(self):
        self.stop_thread = True
        self.stop_measurement = True