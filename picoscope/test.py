#!/usr/bin/env python3

from ps4262 import ps4262
import pylab as plt

ps = ps4262()

i = 0
while i < 5:
    i = i + 1
    while not ps.isReady():
        pass
    (x,y) = ps.getData()
    # plot the data


print (ps.getMetatada())
