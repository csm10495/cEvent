# cEvent
cEvent is a library that allows execution of events via timed intervals via threading.

## Simple Usage Example
```
# import me!
from cevent import EventManager

# create our event manager
mgr = EventManager()

# add a single event for this example. Feel free to add more than 1!
# timeBetweenCalls is in seconds.
mgr.addEvent(thingToCall=lambda:print("Hi"), timeBetweenCalls=1)

'''
As an example, we could have a callback field in addEvent to have the callback (function) get called
  along with the result of the thingToCall function.
import time
mgr.addEvent(thingToCall=lambda: time.time(), timeBetweenCalls=2, callback=lambda ret: print(ret)) 

# in the above example, ret in the callback would be the time.time() returned from thingToCall.
'''

# start the EventManager
mgr.start()

# now Hi will get printed every second

# to stop the EventManager, call stop()
mgr.stop() # will block until stopped
```

## For More Information
Feel free to check out the docstrings in the code and the ```if __name__ == '__main__':``` code in cevent.py.

### How to Install
```
pip install cEvent
```
