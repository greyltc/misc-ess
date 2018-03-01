#!/usr/bin/env python3

from ps4262 import ps4262
import pylab as plt
import time

voltageRange = 5 # volts
requestedSamplingInterval = 1e-6 # seconds
captureDuration = 0.3 # seconds
triggersPerMinute = 30

ps = ps4262(VRange = voltageRange, requestedSamplingInterval = requestedSamplingInterval, tCapture = captureDuration, triggersPerMinute = triggersPerMinute)
time.sleep(3)
ps.setFGen(triggersPerMinute=240)
time.sleep(2)
ps.setFGen(triggersPerMinute=0)
time.sleep(10)
ps.setFGen(triggersPerMinute=-1)
time.sleep(0.05)
ps.setFGen(triggersPerMinute=-1)
time.sleep(0.05)
ps.setFGen(triggersPerMinute=-1)
time.sleep(0.05)
ps.setFGen(triggersPerMinute=-1)
time.sleep(0.05)
ps.setFGen(triggersPerMinute=-1)
time.sleep(0.05)
#ps.setFGen(triggersPerMinute=240)
time.sleep(3)
ps.enable = False
time.sleep(2)
print(60)
ps.setFGen(triggersPerMinute=60)



time.sleep(10)

print(0)
ps.setFGen(triggersPerMinute=0)


time.sleep(10)

print("one pulse")
ps.setFGen(triggersPerMinute=-1)
time.sleep(5)

# clean up the picoscope by deleting it which calls its deconstructor
del(ps)

time.sleep(30) # give the user a chance to look at the plots
