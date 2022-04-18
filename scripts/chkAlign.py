#!/usr/bin/env python3

# Show event streams from old and new timing systems
#
from __future__ import print_function
import argparse
import copy
import epics
import sys
import time


parser = argparse.ArgumentParser(description='Show event streams from old and new timing systems.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', '--old', default='', help='Prefix for old timing system record names')
parser.add_argument('-n', '--new', default='test', help='Prefix for new timing system record names')
args = parser.parse_args()

def PV(pvname=None, **kws):
    pv = epics.PV(pvname, **kws)
    if not pv.wait_for_connection():
        print("Can't connect to %s" % (pvname))
        sys.exit(1)
    return pv

testPatternUpdated = False
def testPatternCallback(pvname=None, value=None, **kws):
    global testPatternUpdated
    if testPatternUpdated: print('New system overrun')
    testPatternUpdated = True
        
def caget(pvname, expect):
    value = PV(pvname).get()
    if value != 1:
        print("%s = %d, expect %d" % (value, expect))
        sys.exit(2)

caget('testTimPotentate', 1)
caget('testEVG:INJ:injCycleEnable', 1)
caget('testTimAllEVRvalid', 1)

gunBunchToInjFieldTrigger = PV(args.old+'GunBunchToInjFieldTrigger', auto_monitor=True)
testGunBunchToInjFieldTrigger = PV(args.new+'GunBunchToInjFieldTrigger', auto_monitor=True)
testGunBunchToInjFieldTrigger.put(gunBunchToInjFieldTrigger.value,wait=True)
print(testGunBunchToInjFieldTrigger.pvname, testGunBunchToInjFieldTrigger.get())

timInjReq = PV(args.old+'TimInjReq', auto_monitor=True, form='time')
evCodes = PV(args.old+'LI11:EVG1-SoftSeq:0:EvtCode-SP', auto_monitor=True, form='time')
evTimes = PV(args.old+'LI11:EVG1-SoftSeq:0:Timestamp-SP', auto_monitor=True, form='time')

testTimInjReq = PV(args.new+'TimInjReq')
testSeqStatus = PV(args.new+'EVG:E1:seqStatus', auto_monitor=True)
testPattern = PV(args.new+'EVG:E1:SEQ1', auto_monitor=True, callback=testPatternCallback)

while True:
    #
    # Wait for next update from old timing system
    #
    then = timInjReq.timestamp
    while timInjReq.timestamp == then: time.sleep(0.05)
    print(then, timInjReq.timestamp)
    injReq = copy.copy(timInjReq.value)
    while evCodes.timestamp <= timInjReq.timestamp: time.sleep(0.05)
    eventList = copy.copy(evCodes.value)
    while evTimes.timestamp <= timInjReq.timestamp: time.sleep(0.05)
    delayList = copy.copy(evTimes.value)

    
    # 
    # Wait for end of new timing system cycle 
    #
    while (testSeqStatus.value & 0x10) == 0: time.sleep(0.05);
    while (testSeqStatus.value & 0x10) != 0: time.sleep(0.05);

    #
    # Request new timing cycle to match old
    #
    testPatternUpdated = False
    testTimInjReq.put(injReq)
    while not testPatternUpdated: time.sleep(0.05)
    newPattern = copy.copy(testPattern.value)

    print(injReq)
    oldDone = False
    newDone = False
    oldIndex = 0
    newIndex = 0
    oldTs = -1
    while not oldDone or not newDone:
        if newIndex >= (len(newPattern) - 1): newDone = True
        if newDone:
            print("%17s" % (""), end='')
        else:
            print("%8d %3d     " % (newPattern[newIndex], newPattern[newIndex+1]), end='')
            if newPattern[newIndex+1] == 127:
                newDone = True
            else:
                newIndex += 2
        if oldIndex >= len(delayList): oldDone = True
        if not oldDone:
            ts = delayList[oldIndex]
            gap = ts- oldTs - 1
            oldTs = ts
            print("%8d %3d" % (gap, eventList[oldIndex]), end='')
            if eventList[oldIndex] == 127:
                oldDone = True
            else:
                oldIndex += 1
        print("")
    print("======================================")
