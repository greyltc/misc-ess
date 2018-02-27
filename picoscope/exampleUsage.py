#!/usr/bin/env python3

from ps4262 import ps4262
import pylab as plt
import time
import sys

voltageRange = 5 # volts
requestedSamplingInterval = 1e-6 # seconds
captureDuration = 0.3 # seconds
triggersPerMinute = 30

ps = ps4262(VRange = voltageRange, requestedSamplingInterval = requestedSamplingInterval, tCapture = captureDuration, triggersPerMinute = triggersPerMinute)

print("Metadata:")
print (ps.getMetadata())
print("")

def plot(x,y):
    plt.ion()
    plt.figure()
    plt.plot(x, y*1e9)
    plt.grid(True)
    plt.title("Picoscope 4000 waveform")
    plt.ylabel("Current [nA]")
    plt.xlabel("Time [s]")
    #plt.legend()
    plt.show()
    plt.pause(.001)

i = 0
while i < 5:
    i = i + 1
    print("Waiting for data...")
    #data = ps.getData() # this call will block until data is ready
    while len(ps.data) == 0:
        pass
    print("Data ready!")
    data = ps.data.pop()
    x = data["time"]
    y = data["current"]
    print("Drawing plot from trigger number", data["nTriggers"])
    # plot the data
    plot(x,y)
    print("")

print("Trigger frequency is", ps.triggerFrequency, "[Hz]")
time.sleep(2)
ps.setFGen(triggersPerMinute = 240)
print("Trigger frequency set to", ps.triggerFrequency, "[Hz]")
time.sleep(5)

print("We've seen", ps.edgesCaught, "triggers since the beginning of time.")

# this is the only way I can get the threads to shutdown gracefully
ps.enable = False

time.sleep(10) # give the user a chance to look at the plots

# reset the global trigger count to 0
ps.resetTriggerCount()

