from scavenger import Scavenger, shutdown, scavenge
from time import sleep

# Sleep for a little while to allow surrogates to be discovered.
print "Sleeping for a little while...",
sleep(1.2)
print "done"
print "Found", len(Scavenger.get_peers()), "surrogates"

@scavenge('0.00001', '0.00001')
def add(x, y):
    return x + y

print "Scavenging a little..."
print add(1,2)
print add(3,4)
print "done"


print 'Doing some manual "scavenging"'
print Scavenger.scavenge('daimi.test.add', [1,2], """
def perform(x,y):
    return x+y
""")
print Scavenger.scavenge('daimi.test.add', [2,3])
print "done"

shutdown()
    

