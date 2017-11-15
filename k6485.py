# written by grey@christoforo.net
# on 15 Nov 2017

import serial
import time
import sys

class K6485:
  """keithley 6485 library
  """
  port = None
  expectedDeviceString = 'KEITHLEY INSTRUMENTS INC.,MODEL 6485,4038279,C01   Jun 23 2010 12:22:00/A02  /H\r\n'
  outOnSettleTime = 0.5 # seconds to settle after output turned on
  def __init__(self, port='/dev/ttyUSB0', baud=57600, timeout=30):
    """keithley 6485 library constructor
    """

    # flush the read buffer here
    self.port = serial.Serial(port,baud,timeout=1)
    self._write('*RST')
    self.port.flush()
    if sys.version_info[0] > 3:
      self.port.reset_output_buffer()
      self.port.reset_input_buffer()
    c = b'c'
    while c is not b'':
      c = self.port.read()
      #print('Flush Read:', c)
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
    
  def currentSetup(self,nplc=10.0,nMean=1,t=False):
    """Setup sourcemeter for current measurements
    """
    cmds = """*RST
      :SYST:ZCH ON
      :CURR:RANG 2e-9
      INIT
      :SYST:ZCOR:ACQ
      :SYST:ZCOR ON
      :CURR:RANG MIN
      :SYST:ZCH OFF
      """
    cmds = cmds.splitlines()
    cmds.append(':CURR:NPLC {:}'.format(nplc))
    
    if t == False:
      cmds.append(':FORM:ELEM READ')
    elif t == True:
      cmds.append(':FORM:ELEM READ, TIME')
    else:
      print('ERROR: time parameter data type')
      cmds.append(':FORM:ELEM READ')
    
    nMean = int(nMean)
    if nMean == 1:
      cmds.append(':SENS:AVER:STAT 0')
    elif (nMean > 1) and (nMean <= 100):
      cmds.append(':SENS:AVER:STAT 1')
      cmds.append(':SENS:AVER:TCON REP')
      cmds.append(':SENS:AVER:STAT {:}'.format(nMean))
    else:
      print('ERROR: Got invalid nMean value')
    
    for cmd in cmds:
      cmd = cmd.strip()
      #print('Sending', cmd)
      self._write(cmd)
      #print(self._qu('STAT:QUE?'))
      
  def getCurrent(self):
    """Reads current from sourcemeter
    """    
    vals = self._qu('READ?').split(',')
    if len(vals) == 1:
      ret = float(vals[0])
    else:
      ret = [float(val) for val in vals ]
    return(ret)
