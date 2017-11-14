# written by grey@christoforo.net
# on 8 Nov 2017

import serial
import time
import sys

class K24xx:
  """keithley 24xx library
  """
  port = None
  expectedDeviceString = 'KEITHLEY INSTRUMENTS INC.,MODEL 2410,4090615,C33   Mar 31 2015 09:32:39/A02  /J/K\r\n'
  outOnSettleTime = 0.5 # seconds to settle after output turned on
  def __init__(self, port='/dev/ttyUSB0', baud=9600, timeout=30):
    """keithley 24xx library constructor
    """

    # flush the read buffer here
    self.port = serial.Serial(port,baud,timeout=0.5)
    self.port.flush()
    if sys.version_info[0] > 3:
      self.port.reset_output_buffer()
      self.port.reset_input_buffer()
    c = b'c'
    while c is not b'':
      c = self.port.read()
    self.port.close()

    self.port = serial.Serial(port,baud,timeout=timeout)
    identStr = self._qu('*IDN?')
    
    if identStr == self.expectedDeviceString:
      pass
      #print('Conected to', deviceString.decode("utf-8"))
    else:
      print('ERROR: Got unexpected device string:', identStr)
      self.port.close()
      
  def __del__(self):
    """keithley 24xx library deconstructor
    """
    #print('Cleaning up sourcemeter comms')
    try:
      self._write(':OUTP OFF')
      self.port.flush()
      time.sleep(0.1)
    except:
      pass
    
    try:
      self.port.reset_output_buffer()
    except:
      pass

    try:
      self.port.reset_input_buffer()
    except:
      pass
    
    try:
      self.port.close()
    except:
      pass
    
  def _write(self,cmd):
    """Send command to sourcemeter
    """
    toSend = cmd.encode('utf-8') + b'\n'
    self.port.write(toSend)
    
  def _qu(self,cmd):
    """Query sourcemeter with command
    """    
    self._write(cmd)
    result = self.port.readline()
    decoded = result.decode('utf-8')
    return(decoded)
    
  def currentSetup(self,nplc=10.0,nMean=1):
    """Setup sourcemeter for current measurements
    """
    cmds = []
    cmds.append('*RST')
    cmds.append(':SOUR:FUNC VOLT')
    cmds.append(':SOUR:VOLT:MODE FIXED')
    cmds.append(':SENS:FUNC "CURR"')
    cmds.append(':SENS:CURR:NPLC {:}'.format(nplc))
    cmds.append(':SOUR:VOLT:RANG MIN')
    cmds.append(':SOUR:VOLT:LEV 0')
    cmds.append(':FORM:ELEM CURR')
    
    nMean = int(nMean)
    if nMean == 1:
      cmds.append(':SENS:AVER:STAT 0')
    elif (nMean > 1) and (nMean <= 100):
      cmds.append(':SENS:AVER:STAT 1')
      cmds.append(':SENS:AVER:STAT {:}'.format(nMean))
    else:
      print('ERROR: Got invalid nMean value')
    
    for cmd in cmds:
      #print('Sending', cmd)
      self._write(cmd)
      #self.port.write(b':SYST:ERR?\n')
      #err = self.port.readline()
      #print(err)

  def setOutput(self,value):
    if value == True:
      self._write(':OUTP ON')
      time.sleep(self.outOnSettleTime) # let the output settle
    elif value == False:
      self._write(':OUTP OFF')
    else:
      print('Invalid data type')
      
  def getCurrent(self):
    """Reads current from sourcemeter
    """    
    current = self._qu('READ?')
    return float(current)
