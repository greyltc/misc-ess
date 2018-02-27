# written by grey@christoforo.net
# on 21 Feb 2018

from picoscope import ps4000
import numpy as np
import threading
import pickle
import time
import concurrent.futures
from collections import deque

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
        self.ps = ps4000.PS4000(blockReadyCB = self.blockReady)
        self.lastTriggerTime = None # stores time of last trigger edge
        self.data = deque()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers = 1)        

        # setup sampling interval
        self._setTimeBase(requestedSamplingInterval = requestedSamplingInterval, tCapture = tCapture)

        # setup current collection channel (A)
        self._setChannel(VRange = VRange)

        # turn on the function generator
        self.setFGen(triggersPerMinute = triggersPerMinute)

        # setup triggering
        self.executor.submit(self.ps.setExtTriggerRange, VRange = 0.5)
        # 0 ms timeout means wait forever for the next trigger
        self.executor.submit(self.ps.setSimpleTrigger, 'EXT', 0.15, 'Rising', delay=0, timeout_ms = 0, enabled=True)
        
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
            
        self.enable = True
        self._run()

    def __del__(self):
        try:
            self.executor.shutdown()
        except:
            pass
        
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
    
    # this can't be called externally (it doesn't go into the executor queue)
    def _fetchData(self):
        voltageData = self.ps.getDataV('A', self.nSamples, returnOverflow=False)
        self.data.append ({"nTriggers": self.edgesCaught, "t0": self.timeVector[0], "t_end": self.timeVector[-1], "current": voltageData * self.currentScaleFactor, "timestamp": self.lastTriggerTime, "yLabel": "Current", "xLabel": "Time", "yUnits": "s", "xUnits": "A"})
        self._run()
        
    def blockReady(self,handle,error,void):
        self.lastTriggerTime = time.gmtime() # returns seconds since 1970 GMT
        self.edgesCaught = self.edgesCaught +  1  # incriment edge count
        pickle.dump(self.edgesCaught,self.fp,-1)
        self.fp.flush()
        self.fp.seek(0)
        
        self.executor.submit(self._fetchData)
        
    def setFGen(self, triggersPerMinute = 10):
        """Sets picoscope function generator parameters
        use triggersPerMinute = 0 to disable the function generator"""
        frequency = triggersPerMinute / 60
        self.triggerFrequency = frequency
        duration = 1/frequency
        
        # for AWG
        nWaveformSamples = 2 ** 12
        waveform = np.zeros(nWaveformSamples)
        
        if frequency > 0:  # run continuously mode
            offsetVoltage = 0.5
            pkToPk = 1
            waveType="Square"
            shots=0
            stopFreq=frequency
            
            # for short pulses using the arbitrary waveform generator
            sPerSample = duration/nWaveformSamples
            samplesPer5ms = int(np.floor(5e-3/sPerSample))
            waveform[0:samplesPer5ms] = 1
            self.executor.submit(self.ps.setAWGSimple, waveform, duration, offsetVoltage=0.0, indexMode="Single", triggerSource='None', pkToPk=2.0, shots=0, triggerType="Rising")
            
            # for 50% duty cycle square wave
            #self.executor.submit(self.ps.setSigGenBuiltInSimple, offsetVoltage=offsetVoltage, pkToPk=pkToPk, waveType=waveType, frequency=frequency, shots=shots, stopFreq=stopFreq)
            
        elif frequency == 0:  # disable signal generator
            duration = 0.1
            waveform = np.zeros(nWaveformSamples)
            self.executor.submit(self.ps.setAWGSimple, waveform, duration, offsetVoltage=0.0, indexMode="Single", triggerSource='None', pkToPk=2.0, shots=1, triggerType="Rising")
            
        else:  # negative frequencys mean single shot mode
            duration = 0.05
            self.triggerFrequency = 0
            sPerSample = duration/nWaveformSamples
            samplesPer5ms = int(np.floor(5e-3/sPerSample))
            waveform[0:samplesPer5ms] = 1            
            self.executor.submit(self.ps.setAWGSimple, waveform, duration, offsetVoltage=0.0, indexMode="Single", triggerSource='None', pkToPk=2.0, shots=1, triggerType="Rising")

    def _setChannel(self, VRange = 2):
        self.VRange = VRange
        self.executor.submit(self.ps.setChannel, channel='A', coupling='DC', VRange=VRange, VOffset=0.0, enabled=True, BWLimited=0, probeAttenuation=1.0)
        #channelRange = self.ps.setChannel(channel='A', coupling='DC', VRange=VRange, VOffset=0.0, enabled=True, BWLimited=0, probeAttenuation=1.0)

    # this can't be called externally (it doesn't go into the executor queue)
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

    def _run(self):
        """
        This arms the trigger
        """
        if self.enable:
            pretrig = 0.1  # 10% of the output data will be from before the trigger event
            self.executor.submit(self.ps.runBlock, pretrig = pretrig, segmentIndex = 0)
            #self.ps.runBlock(pretrig = pretrig, segmentIndex = 0)
            self.timeVector = (np.arange(self.ps.noSamples) - int(round(self.ps.noSamples * pretrig))) * self.actualSamplingInterval
