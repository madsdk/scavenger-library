from scavenger import Scavenger, shutdown, scavenge
from time import sleep

# Sleep for a little while to allow surrogates to be discovered.
print "Sleeping for a little while...",
sleep(1.2)
print "done"

@scavenge('#0', '#0')
def add(x, y):
    return x + y

print "Scavenging a little..."
print add(1,2)
print add(3,4)
print "done"

shutdown()
    

