#!/usr/bin/env python3

from ps4262 import ps4262
import pylab as plt
import time

ps = ps4262()
print (ps.getMetatada())

def plot(x,y):
    plt.ion()
    plt.figure()
    plt.plot(x, y)
    plt.grid(True)
    plt.title("Picoscope 4000 waveform")
    plt.ylabel("Voltage (V)")
    plt.xlabel("Time [s]")
    #plt.legend()
    plt.show()
    plt.pause(.001)

i = 0
while i < 5:
    i = i + 1
    print("Waiting for data...")
    while not ps.isReady():
        pass
    print("Data ready!")
    data = ps.getData() # this call will block until data is ready
    x = data["time"]
    y = data["current"]
    # plot the data
    plot(x,y)

# clean up the picoscope by deleting it which calls its deconstructor
del(ps)

time.sleep(30) # give the user a chance to look at the plots
