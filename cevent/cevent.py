'''
Brief:
    cevent.py - File for cEvent. 
        cEvent allows us to have functions get called via threads on timed intervals.

Author(s):
    Charles Machalow via the MIT License
'''
import atexit
import logging
import sys
import threading
import time
import traceback

LOGGER = logging.getLogger(__name__)

class EventThread(threading.Thread):
    '''
    Brief:
        EventThread is a daemon threading.Thread that can catch an internal exception.
            That internal exception is raised when the thread is join(ed).
    '''
    def __init__(self, *args, **kwargs):
        '''
        Brief:
            Init for EventThread. Passes args/kwargs to threading.Thread.__init__()
            wraps .run() to catch an exception if it is thrown.
        '''
        threading.Thread.__init__(self, *args, **kwargs)
        self._real_run = self.run
        self.run = self._wrapped_run
        self.exception = None
        self.setDaemon(True)
        self.isJoined = False

    def _wrapped_run(self):
        '''
        Brief:
            Called when run() is called to start the thread.
                Will catch an exception if one is raised and save it in self.execption.
        '''
        try:
            self._real_run()
        except Exception as ex:
            self.exception = ex

    def join(self):
        '''
        Brief:
            Indefinitely joins this thread. If we have a saved exception in self.exception,
                will raise it after the join is completed. If the join never completes, we never raise.
        '''
        LOGGER.debug('joining thread: %s' % self.getName())
        
        if self != threading.current_thread():
            threading.Thread.join(self)
        else:
            LOGGER.warning("Not joining thread: %s, as that is this thread. Still marking as joined." % self.getName())

        self.isJoined = True
        if self.exception is not None:
            raise self.exception

class Event(object):
    '''
    Brief:
        A single event managed by the EventManager. It keeps track of when the passed in function should be called,
            along with the threads that may get spawned to perform the event (and possibly a callback)
    '''
    def __init__(self, thingToCall, timeBetweenCalls, spawnThread, callback=None):
        '''
        Brief:
            init for Event. Takes in a function to call when the event fires, along with the time (in seconds) between calls,
                whether or not to spawn an async(ish) thread for the thingToCall, and an optional callback once the 
                    thingToCall is finished.
        '''
        self._callable = thingToCall
        self._timeBetweenCalls = timeBetweenCalls
        self._callback = callback
        self._spawnThread = spawnThread
        self._lastCallTime = 0
        self._threads = []

    def _shouldCall(self):
        '''
        Brief:
            Returns True if we should call the thingToCall based off of waiting enough time (after the lastCallTime to the timeBetweenCalls).
        '''
        return self._lastCallTime + self._timeBetweenCalls < time.time()

    def _call(self, iAmAThread=False):
        '''
        Brief:
            Calls the thingToCall. If we should spawn a thread, and this is not a thread, will spawn an EventThread and start it.
                Once this is called without intent to spawn another thread, wil call the thingToCall and then once finished, call
                    the callback. The lastCallTime is updated just before making the call.
        '''
        if self._spawnThread and not iAmAThread:
            LOGGER.debug("Spawning a thread to call the _callable() (%s)" % self._callable.__name__)
            retVal = EventThread(target=self._call, args=(True,))
            retVal.start()
            self._threads.append(retVal)
        else:
            self._lastCallTime = time.time()    

            retVal = self._callable()
            if self._callback is not None:
                retVal = self._callback(retVal)

        return retVal

    def _joinDeadThreads(self):
        '''
        Brief:
            Goes through all sub-threads of this Event and checks if it is alive. If it isn't, join it.
                After that, remove all threads that were joined.
        '''
        for i in self._threads:
            if not i.is_alive():
                i.join() # our thread's version can raise if the thread generated an exception

        self._threads = [i for i in self._threads if not i.isJoined]

    def callIfShouldCall(self):
        '''
        Brief:
            If we should call, based off of timing, does call the thingToCall.
                After that returns, call _joinDeadThreads().
        '''
        if self._shouldCall():
            retVal = self._call()
            self._joinDeadThreads()
            LOGGER.debug("Thread count: %d" % len(self._threads))

    def join(self):
        '''
        Brief:
            Joins all sub threads. Clears sub-thread list.
        '''
        LOGGER.debug("Requesting that all subthreads join()")
        # join all sub-threads
        for i in self._threads:
            i.join() 

        LOGGER.debug("Clearing the subthreads list")
        self._threads = []

class EventManager(object):
    '''
    Brief:
        The EventManager keeps track of all Events running under it.
            Once started, it will spawn a thread below it to continually check if an event
                should have it's call called.

        It will stop automatically if a child thread raises an exception. That exception will be placed in .childException
    '''
    def __init__(self, eventsSpawnThreads=True):
        '''
        Brief:
            init for EventManager. Takes a variable to say if internal events should spawn threads. If this is True,
                each event call will lead to a thread being spawned so that the _execute() loop can continue async.
        '''
        self._thread = None
        self._shouldContinue = True
        self._running = False
        self._eventList = []
        self._eventsSpawnThreads = eventsSpawnThreads
        self._stopInProgress = False        
        self.childException = None

    def _execute(self):
        '''
        Brief:
            Called in a a thread (by start()). Continually calls all events to run themselves, if they should.
                The internal loop will stop at some point after calling stop()
        '''
        self._running = True
        while self._shouldContinue:
            try:
                for i in self._eventList:
                    i.callIfShouldCall()
            except Exception as ex:
                print ("Stopping EventManager due to child exception:")
                traceback.print_exc()
                self.childException = ex
                break
        self._running = False
            
    def addEvent(self, thingToCall, timeBetweenCalls, callback=None):
        '''
        Brief:
            Can be called at any time to add an event to the EventManager.
                thingToCall - callable to call at every timeBetweenCalls interval
                timeBetweenCalls - Time in seconds between calls to thingToCall
                callback - If given, a callback to call with the result of thingToCall each time.
        '''
        e = Event(thingToCall, timeBetweenCalls, self._eventsSpawnThreads, callback)
        self._eventList.append(e)

    def start(self):
        '''
        Brief:
            Starts the _execute() loop in a sub-thread.
        '''
        LOGGER.debug("Requesting to start the _execute() loop")        
        self._shouldContinue = True
        self._thread = threading.Thread(target=self._execute)
        self._thread.start()

    def stop(self):
        '''
        Brief:
            Requests that the _execute() loop stops. Also joins all subthreads.
                Returns once all current jobs are joined and the EventManager is stopped.
        '''
        if not self._stopInProgress:
            self._stopInProgress = True
            LOGGER.debug("Requesting to stop the _execute() loop. Thread: %s" % threading.current_thread().getName())
            self._shouldContinue = False
            if self._thread is not None:
                self._thread.join()

            # join all events
            for i in self._eventList:
                i.join()

            self._stopInProgress = False

        else:
            LOGGER.warning("nop'ing the stop() call since another stop() is in progress.Thread: %s" % threading.current_thread().getName())

def _printThenSleep(t, p):
    '''
    Brief:
        Sample function to print p then sleep for t. Return time.time()
    '''
    print (p, time.time())
    time.sleep(t)
    return time.time()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    e = EventManager(eventsSpawnThreads=True)
    e.addEvent(lambda: _printThenSleep(3, '3'), 1, callback=lambda x: e.stop())

    realExit = exit
    def exit(*args, **kwargs):
        # stop all event managers
        for key, value in globals().items():
            if isinstance(value, EventManager):
                try:
                    value.stop()
                except:
                    pass
        realExit(*args, **kwargs)
    quit = exit

    e.start()