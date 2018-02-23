# written by grey@christoforo.net
# on 21 Feb 2018

from picoscope import ps4000
import numpy as np
import threading
import pickle

class BaseThread(threading.Thread):
    def __init__(self, callback=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target

    def target_with_callback(self):
        self.method()
        if self.callback is not None:
            self.callback()

class ps4262:
    """
    picotech PS4262 library
    """
    currentScaleFactor = 1/10000000 # amps per volt through our LPM7721 eval board
    persistentFile = '/var/tmp/edgeCount.bin'
    def __init__(self, VRange = 5, requestedSamplingInterval = 1e-6, tCapture = 0.3, triggersPerMinute = 30):
        """
        picotech PS4262 library constructor
        """
        # this opens the device
        self.ps = ps4000.PS4000()
        self.edgeCounterEnabled = False

        # setup sampling interval
        self._setTimeBase(requestedSamplingInterval = requestedSamplingInterval, tCapture = tCapture)

        # setup current collection channel (A)
        self._setChannel(VRange = VRange)

        # turn on the function generator
        self.setFGen(triggersPerMinute = triggersPerMinute)

        # setup triggering
        self.ps.setExtTriggerRange(VRange = 0.5)
        # 0 ms timeout means wait forever for the next trigger
        self.ps.setSimpleTrigger('EXT', 0.25, 'Rising', delay=0, timeout_ms = 0, enabled=True)

        
        try:
            self.fp = open(self.persistentFile, mode='r+b')
            self.edgesCaught = pickle.load(self.fp)
            self.fp.seek(0)
        except:
            self.edgesCaught = 0
            self.fp = open(self.persistentFile, mode='wb')
            pickle.dump(self.edgesCaught,self.fp,-1)
            self.fp.flush()
            self.fp.seek(0)
            
        self.data = None
        self.edgeCounterEnabled = True
        # start the trigger detection thread and the data collection
        self._runThread()

    def __del__(self):        
        try:
            self.ps.stop()
        except:
            pass
        
        try:
            self.ps.close()
        except:
            pass
        
        try:
            self.fp.close()
        except:
            pass
        
    def resetTriggerCount(self):
        self.edgesCaught = 0
        pickle.dump(self.edgesCaught,self.fp,-1)
        self.fp.flush()
        self.fp.seek(0)
    
    def _runThread(self):
        """create a new trigger detection thread and run it"""
        self._run()
        self.edgeThread = BaseThread( name='edgeWatcher', target=self.ps.waitReady,\
                                      callback=self._edgeDetectCallback)
        
        self.edgeThread.start()
    
    # this gets called when a trigger has been seen
    def _edgeDetectCallback(self):
        self.edgesCaught = self.edgesCaught +  1  # incriment edge count
        pickle.dump(self.edgesCaught,self.fp,-1)
        self.fp.flush()
        self.fp.seek(0)
        
        # store away the scope data
        voltageData = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
        self.data = {"nTriggers": self.edgesCaught, "time": self.timeVector, "current": voltageData * self.currentScaleFactor} 
        
        if self.needFGenUpdate:
            self.edgeCounterEnabled = False
            self.setFGen(triggersPerMinute=self.triggersPerMinute)
            self.edgeCounterEnabled = True
        # now spawn a new trigger detection thread
        if self.edgeCounterEnabled:
            self._runThread()

            
    def setFGen(self, triggersPerMinute = 10):
        """Sets picoscope function generator parameters
        use triggersPerMinute = 0 to disable the function generator"""
        self.triggersPerMinute = triggersPerMinute
        frequency = triggersPerMinute / 60
        self.triggerFrequency = frequency
        
        if frequency > 0:
            offsetVoltage = 0.5
            pkToPk = 1
            waveType="Square"
            shots=0
            stopFreq=frequency
        else:
            pkToPk = 0
            waveType="DC"
            frequency=1
            stopFreq=1
            shots=1
        if self.edgeCounterEnabled:
            self.needFGenUpdate = True
        else:
            self.ps.setSigGenBuiltInSimple(offsetVoltage=offsetVoltage, pkToPk=pkToPk, waveType=waveType, frequency=frequency, shots=shots, stopFreq=stopFreq)
            self.needFGenUpdate = False

    def _setChannel(self, VRange = 2):
        self.VRange = VRange
        channelRange = self.ps.setChannel(channel='A', coupling='DC', VRange=VRange, VOffset=0.0, enabled=True, BWLimited=0, probeAttenuation=1.0)

    def _setTimeBase(self, requestedSamplingInterval=1e-6, tCapture=0.3):
        self.requestedSamplingInterval = requestedSamplingInterval
        self.tCapture = tCapture
        
        (self.actualSamplingInterval, self.nSamples, maxSamples) = \
            self.ps.setSamplingInterval(sampleInterval = requestedSamplingInterval, duration = tCapture, oversample=0, segmentIndex=0)

    def getMetadata(self):
        """
        Returns metadata struct
        """
        metadata = {"Voltage Range" : self.VRange,
        "Trigger Frequency": self.triggerFrequency,
        "Requested Sampling Interval": self.requestedSamplingInterval,
        "Capture Time": self.tCapture}
        return metadata

    def getData(self):
        """
        Returns two np arrays:
        time in seconds since trigger (can be negative)
        current in amps
        """
        while self.data is None:
            pass
        retVal = self.data
        self.data = None
        return retVal

    def _run(self):
        """
        This arms the trigger
        """
        pretrig = 0.1  # 10% of the output data will be from before the trigger event
        self.ps.runBlock(pretrig = pretrig, segmentIndex = 0)
        self.timeVector = (np.arange(self.ps.noSamples) - int(round(self.ps.noSamples * pretrig))) * self.actualSamplingInterval
