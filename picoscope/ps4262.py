# written by grey@christoforo.net
# on 21 Feb 2018

from picoscope import ps4000

class PS4262:
  """
  picotech PS4262 library
  """
  currentScaleFactor = 1.0 # amps per volt
  def __init__(self, VRange = 2, requestedSamplingInterval = 1e-6, tCapture = 0.3, triggersPerMinute = 10):
    """
    picotech PS4262 library constructor
    """

    # this opens the device
    self.ps = ps4000.PS4000()

    # setup sampling interval
    self.setTimeBase(requestedSamplingInterval = requestedSamplingInterval, tCapture = 0.3)

    # setup current collection channel (A)
    self.setChannel(VRange = VRange)

    # turn on the function generator
    self.setFgen(enabled = True, triggersPerMinute = triggersPerMinute)

    # setup triggering
    self.ps._lowLevelSetExtTriggerRange(VRange = 5)
    ps.setSimpleTrigger('EXT', 0.1, 'Rising', delay=0, timeout_ms = 1000 / self.triggerFrequency, enabled=True)

    # start the collection
    self.run()

  def __del__(self):
    """
    picotech PS4262 librarydeconstructor
    """
    #print('Cleaning up sourcemeter comms')
    try:
        self.ps.stop()
        self.ps.close()
    except:
      pass

  def setFGen(self, enabled = True, triggersPerMinute = 10):
      frequency = 60 / triggersPerMinute
      self.triggerFrequency = frequency
      if enabled is True:
          self.ps.setSigGenBuiltInSimple(offsetVoltage=0.5,pkToPk=1,WaveType="Square", frequency=frequency, shots=0, stopFreq=frequency)
      else:
          self.ps.setSigGenBuiltInSimple(offsetVoltage=0,pkToPk=0,WaveType="DC", frequency=1, shots=1, stopFreq=1)

  def setChannel(self, VRange = 2):
      self.VRange = VRange
      channelRange = ps.setChannel(channel='A', coupling='DC', VRange=VRange, VOffset=0.0, enabled=True, BWLimited=0, proveAttenuation=1.0)

  def setTimeBase(self, requestedSamplingInterval=1e-6, tCapture=0.3):
    self.requestedSamplingInterval = requestedSamplingInterval
    self.tCapture = tCapture
    # setup timebase here
    self.nSamples = nSamples
    self.actualSampleInterval = actualSampleInterval

 def getMetatada(self):
     """
     Returns metadata struct
     """
     metaData = {"Voltage Range" : self.Vrange,
     "Trigger Frequency": self.triggerFrequency,
     "Requested Sampling Interval": self.requestedSamplingInterval,
     "Capture Time": self.tCapture}
     return metaData

  def getData(self):
      """
      Returns two np arrays:
      time in seconds since trigger (can be negative)
      current in amps
      """
      voltageData = self.ps.getDataV('A', nSamples, returnOverflow=False)
      # once someone has collected the data, it's time to run again
      self.run()
      return (self.timeVector, voltageData * currentScaleFactor)

  def run(self):
      """
      This arms the trigger
      """
      pretrig = 0.1
      self.ps.runBlock(pretrig = pretrig, segmentIndex = 0)
      self.timeVector =

  def isReady(self):
    """Send command to sourcemeter
    """
    return self.ps.isReady()
