#!/usr/bin/env python3

# Show event streams from old and new timing systems
#
from __future__ import print_function
import argparse
import copy
import datetime
import epics
import sys
import time


parser = argparse.ArgumentParser(description='Show event streams from old and new timing systems.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--old', default='', help='Prefix for old timing system record names')
parser.add_argument('-n', '--new', default='test', help='Prefix for new timing system record names')
parser.add_argument('-i', '--internal', action='store_true', help="Use internall-generated timInjReq (and not the value from the  old system)")
args = parser.parse_args()

def PV(pvname=None, **kws):
    pv = epics.PV(pvname, **kws)
    if not pv.wait_for_connection():
        print("Can't connect to %s" % (pvname))
        sys.exit(1)
    return pv

def caget(pvname, expect):
    value = PV(pvname).get()
    if value != 1:
        print("%s = %d, expect %d" % (value, expect))
        sys.exit(2)

def showVector(pv, showTime):
    t = pv.get()
    print(pv.pvname, '[', end='')
    for f in t[0:-1]: print("%.9g " % (f), end='')
    print("%g]" % (t[-1]), end='')
    if showTime: print("  %s" % (
                         datetime.datetime.fromtimestamp(pv.timestamp).strftime(
                                               "%Y-%m-%d %H:%M:%S.%f")), end='')
    print("")

caget('testTimPotentate', 1)
caget('testEVG:INJ:injCycleEnable', 1)
caget('testTimAllEVRvalid', 1)

gunBunchToInjFieldTrigger = PV(args.old+'GunBunchToInjFieldTrigger', auto_monitor=True)
testGunBunchToInjFieldTrigger = PV(args.new+'GunBunchToInjFieldTrigger', auto_monitor=True)
testGunBunchToInjFieldTrigger.put(gunBunchToInjFieldTrigger.value,wait=True)
showVector(testGunBunchToInjFieldTrigger, False)

timInjReq = PV(args.old+'TimInjReq', auto_monitor=True)
evCodes = PV(args.old+'LI11:EVG1-SoftSeq:0:EvtCode-SP', auto_monitor=True)
evTimes = PV(args.old+'LI11:EVG1-SoftSeq:0:Timestamp-SP', auto_monitor=True)
timInjFieldSyncDelay = PV('TimInjFieldSyncDelay', auto_monitor=True)
timExtrFieldSyncDelay = PV('TimExtrFieldSyncDelay', auto_monitor=True)

testTimInjReq = PV(args.new+'TimInjReq')
testSeqStatus = PV(args.new+'EVG:E1:seqStatus', auto_monitor=True)
testPattern = PV(args.new+'EVG:E1:SEQ1', auto_monitor=True)

time.sleep(0.05)
injReq = [1, 4, 40, 0, 1818324, 60231150, int(time.time())]
matchCount = 0
differenceCount = 0
overrunCount = 0
while True:
    if args.internal:
        injReq[6] += 1
        eventList = []
        delayList = []
    else:
        #
        # Wait for next update from old timing system
        #
        time.sleep(0.05)
        injReq[6] = timInjReq.value[6]
        while timInjReq.value[6] == injReq[6]: time.sleep(0.05)
        injReq = copy.copy(timInjReq.value)
        injReq[4] = timInjFieldSyncDelay.value
        injReq[5] = timExtrFieldSyncDelay.value
        while evCodes.timestamp <= timInjReq.timestamp: time.sleep(0.05)
        eventList = copy.copy(evCodes.value)
        while evTimes.timestamp <= timInjReq.timestamp: time.sleep(0.05)
        delayList = copy.copy(evTimes.value)
        if evCodes.timestamp > (timInjReq.timestamp + 1.32) \
        or evTimes.timestamp > (timInjReq.timestamp + 1.32):
            overrunCount += 1
            print("Overrun %.6f %.6f %.6f" % (timInjReq.timestamp,
                                          evCodes.timestamp, evTimes.timestamp))
            continue

    #
    # Wait for end of new timing system cycle
    #
    while (testSeqStatus.value & 0x10) == 0: time.sleep(0.05);
    while (testSeqStatus.value & 0x10) != 0: time.sleep(0.05);

    #
    # Request new timing cycle to match old
    #
    testTimInjReq.put(injReq, wait=True)

    #
    # Wait for new timing sequence
    #
    passCount = 0
    while testPattern.timestamp <= testTimInjReq.timestamp:
        if passCount >= 20:
            passsCount = 100
            break
        time.sleep(0.05)
        passCount += 1
    if passCount == 100:
        print("No new sequence")
        continue
    newPattern = copy.copy(testPattern.value)

    #
    # Show new and old sequences
    #
    showVector(testTimInjReq, True)
    oldActive = True
    newActive = True
    oldIndex = 0
    newIndex = 0
    oldTs = -1
    oldIndexOffset = -1
    match = True
    while oldActive or newActive:
        if newIndex >= (len(newPattern) - 1): newActive = False
        if newActive:
            newGap = newPattern[newIndex]
            newEvent = newPattern[newIndex+1]
            print("%8d %3d     " % (newGap, newEvent), end='')
            if newPattern[newIndex+1] == 127:
                newActive = False
            else:
                newIndex += 2
        else:
            print("%17s" % (""), end='')
        if oldIndex >= len(delayList): oldActive = False
        if oldActive:
            ts = delayList[oldIndex]
            oldGap = ts- oldTs - 1
            oldTs = ts
            print("%8d %3d" % (oldGap, eventList[oldIndex]), end='')
            if eventList[oldIndex] == 127:
                oldActive = False
            else:
                oldIndex += 1
        if oldActive and newActive and match and (oldIndex > 1):
            oldGap = delayList[oldIndex+oldIndexOffset] - delayList[oldIndex+oldIndexOffset-1] - 1
            if (newGap != oldGap) or \
               (newEvent != eventList[oldIndex+oldIndexOffset]):
                oldGap = delayList[oldIndex] - delayList[oldIndex - 2] - 1
                oldIndexOffset += 1
                if (newGap != oldGap) or \
                   (newEvent != eventList[oldIndex+oldIndexOffset]):
                    print(" --- CHANGE", end='')
                    differenceCount += 1
                    match = False
        print("")
    if match: matchCount += 1
    print("================= Matches: %d   Differences: %d   Overruns: %d" %
                                    (matchCount, differenceCount, overrunCount))
