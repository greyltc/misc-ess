# written by grey@christoforo.net
# on 21 Feb 2018

from picoscope import ps4000
import numpy as np
import threading
import pickle
import time

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
        self.lastTriggerTime = None
        self.data = None

        # setup sampling interval
        self._setTimeBase(requestedSamplingInterval = requestedSamplingInterval, tCapture = tCapture)

        # setup current collection channel (A)
        self._setChannel(VRange = VRange)

        # turn on the function generator
        self.setFGen(triggersPerMinute = triggersPerMinute)

        # setup triggering
        self.ps.setExtTriggerRange(VRange = 0.5)
        # 0 ms timeout means wait forever for the next trigger
        self.ps.setSimpleTrigger('EXT', 0.15, 'Rising', delay=0, timeout_ms = 0, enabled=True)
        
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
        self.edgeThread = BaseThread( name='edgeWatcher', target=self.ps.waitReady,\
                                      callback=self._edgeDetectCallback)
        
        self.edgeThread.start()
    
    # this gets called when a trigger has been seen
    def _edgeDetectCallback(self):
        self.lastTriggerTime = time.gmtime() # returns seconds since 1970 GMT
        self.edgesCaught = self.edgesCaught +  1  # incriment edge count
        pickle.dump(self.edgesCaught,self.fp,-1)
        self.fp.flush()
        self.fp.seek(0)
        
        # store away the scope data
        voltageData = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
        self.data = {"nTriggers": self.edgesCaught, "time": self.timeVector, "current": voltageData * self.currentScaleFactor, "timestamp": self.lastTriggerTime} 
        
        if self.needFGenUpdate:
            self.edgeCounterEnabled = False
            self.setFGen(triggersPerMinute=self.triggersPerMinute)
        else:
            if self.singleShotPending:
                self.singleShotPending = False
                self.edgeCounterEnabled = False  # disable edge counter because we just got a single shot
            if self.edgeCounterEnabled:
                self._run()  # initiate data collection
                self._runThread() # spawn a new trigger detection thread
            
    def setFGen(self, triggersPerMinute = 10, oneShot = False):
        """Sets picoscope function generator parameters
        use triggersPerMinute = 0 to disable the function generator
        use any negative value to send a single shot trigger immediately"""
        self.triggersPerMinute = triggersPerMinute
        frequency = triggersPerMinute / 60
        self.triggerFrequency = frequency
        duration = 1/frequency
        
        if frequency > 0:  # normal pulse train mode
            offsetVoltage = 0.5
            pkToPk = 1
            waveType="Square"
            shots = 0
            stopFreq = frequency
            self.singleShotPending = False
            triggerSource = "None"
            triggerType = "Rising"
        elif frequency == 0: # FGen off mode
            offsetVoltage = 0
            pkToPk = 0
            offsetVoltage = 0
            waveType="DC"
            frequency=1
            stopFreq=1
            shots=1
        if self.edgeCounterEnabled:
            self.needFGenUpdate = True
        else:
            nWaveformSamples = 2 ** 12
            sPerSample = duration/nWaveformSamples
            samplesPer5ms = int(np.floor(5e-3/sPerSample))
            
            waveform = np.zeros(nWaveformSamples)
            waveform[0:samplesPer5ms] = 1
        
            (waveform_duration, deltaPhase) = self.ps.setAWGSimple(
                waveform, duration, offsetVoltage=0.0,
                indexMode="Single", triggerSource='None', pkToPk=2.0, shots=0, triggerType="Rising")            
            #self.ps.setSigGenBuiltInSimple(offsetVoltage=offsetVoltage, pkToPk=pkToPk, waveType=waveType, frequency=frequency, shots=shots, stopFreq=stopFreq)
            self.needFGenUpdate = False
            if triggersPerMinute != 0: # only count edges if the FGen will be running
                self.edgeCounterEnabled = True
                self._runThread()
            else:
                self.edgeCounterEnabled = False
                

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
            if not self.edgeCounterEnabled and self.data is None:
                print("There is no data and there will never be any!")
                return None
        retVal = self.data
        self.data = None
        return retVal

    def _run(self):
        """
        This arms the trigger
        """
        pretrig = 0.5  # 10% of the output data will be from before the trigger event
        self.ps.runBlock(pretrig = pretrig, segmentIndex = 0)
        self.timeVector = (np.arange(self.ps.noSamples) - int(round(self.ps.noSamples * pretrig))) * self.actualSamplingInterval
