#!/usr/bin/env python3

# written by grey@christoforo.net
# on 8 Nov 2017

# prints current from keithley connected via serial

from k24xx import K24xx
from k6485 import K6485
import sys
import argparse

# for cmd line arguments
parser = argparse.ArgumentParser(description='Reads current from Keithley thing')
parser.add_argument('-p','--port', dest='port', type=str, default='/dev/ttyUSB0', help='Serial port the sourcemeter is connected to')
parser.add_argument('-b','--baud', dest='baud', type=int, default=57600, help='Serial port comms baud rate')
parser.add_argument('-t','--timeout', dest='timeout', type=int, default=30, help='Comms timeout [s]')
parser.add_argument('-a','--average', dest='meanValues', type=int, default=1, help='Number of values to internally average')
parser.add_argument('-c','--nplc', dest='nplc', type=float, default=10.0, help='Number of power line cycles to integrate over when measuring')
parser.add_argument('-s','--timestamp', dest='time', action='store_true', default=False, help='Print out timestamp with current value')
parser.add_argument('-n','--measurements', dest='n', type=int, default=1, help='Number of measurements to make (-1 for infinty)')
parser.add_argument('-k','--keithley', dest='series', type=int, default=6, help='Keithley series number to talk to (4 or 6)')

args = parser.parse_args()

if args.series == 4:
  k = K24xx(baud=args.baud, port=args.port, timeout=args.timeout)
elif args.series == 6:
  k = K6485(baud=args.baud, port=args.port, timeout=args.timeout)
else:
  print('ERROR: bad series value')
  exit(-1)

k.currentSetup(nplc=args.nplc, nMean=args.meanValues, t=args.time)
if args.series == 4:
  k.setOutput(True)

m = 0
while True:
  if args.time == True:
    [current, time] = k.getCurrent()
    print(time,', ',current)
  else:
    current = k.getCurrent()
    print(current)
  m = m + 1

  if args.n == m:
      break

if args.series == 4:
  k.setOutput(False)

sys.exit(0)
