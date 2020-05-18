#!/usr/bin/env python

from __future__ import print_function
import csv
import sys
import re

EventColumn      = -1
OffsetColumn     = -1
ExpressionColumn = -1
TickOffsetColumn = -1

modeDict = { }
eventDict = { }

def match(pattern, string):
    return re.match(pattern, string, re.IGNORECASE)

def number(str, lineno):
    if match('^[\s]*$', str):
        return 0
    elif match('^[\s]*[\d-]+[\s]*$', str):
        return int(str)
    else:
        print("Line %d -- Error: Bad offset %s" % (lineno, str), file=sys.stderr)
        sys.exit(1)

with open('TuningModeTriggers.csv', newline='') as csvFile:
    reader = csv.reader(csvFile)
    lineno = 0
    inHeader = True
    lastEvent = 0
    for line in reader:
        lineno += 1
        if inHeader:
            # Look for descriptive column headers
            if match('Mode[\s]Number', line[0]):
                for c in range(0, len(line)):
                    val = line[c]
                    if match('[\d]+', val):
                        modeDict[val] = {'column':c, 'events':[]}
                    if match('Number', val): EventColumn = c
                    if match('Timestamp[\s]Offset', val): OffsetColumn = c
                    if match('Functional[\s]Time', val): ExpressionColumn = c
                    if match('Offset[\s]\[Ticks\]', val): TickOffsetColumn = c
                if EventColumn < 0  \
                 or OffsetColumn < 0 \
                 or ExpressionColumn < 0 \
                 or TickOffsetColumn < 0 \
                 or len(modeDict) == 0:
                    print("Line %d -- Error: Bad heading" % (lineno), file=sys.stderr)
                    sys.exit(1)
                inHeader = False
        else:
            evt = line[EventColumn]
            if match('^[\s]*[\d]+[\s]*$', evt):
                evt = int(evt)
                if evt == 127: break
                if evt <= 0 or evt > 255:
                    print("Line %d -- Error: Bad event number" % (lineno), file=sys.stderr)
                    sys.exit(1)
                if evt < lastEvent:
                    print("Line %d -- Warning: Event out of order -- line ignored" % (lineno), file=sys.stderr)
                    continue
                # Canonicalize expression
                lastEvent = evt
                expr = line[ExpressionColumn]
                if match('^[\s]*$', expr) or match('^[\s]*Start[\s]*$', expr):
                    expr = "0"
                elif match('^[\s]*End', expr):
                    expr = "END_OF_SEQUENCE_TICKS"
                else:
                    expr = re.sub('InjFieldSync', 'injFieldSync', expr, re.IGNORECASE)
                    expr = re.sub('GunBunchDelay', 'gunBunchesDelay', expr, re.IGNORECASE)
                    expr = re.sub('#[\s]*Bunches', 'numBunches', expr, re.IGNORECASE)
                    expr = re.sub('ExtrFieldSync', 'extrFieldSync', expr, re.IGNORECASE)
                    expr = re.sub('TargetBucket', 'targetBucket', expr, re.IGNORECASE)
                    expr = re.sub('[\s]+', '', expr)
                    expr = re.sub('\+', ' + ', expr)
                # Stash info
                offset = number(line[OffsetColumn], lineno)
                tickOffset = number(line[TickOffsetColumn], lineno)
                eventDict[evt] = [expr, offset, tickOffset]
                # Note modes for which event is active
                for mode, modeInfo in modeDict.items():
                    isActive = line[modeInfo['column']]
                    if match('[\s]*x[\s]*', isActive):
                        evtList = modeInfo['events']
                        if not evt in evtList:
                            evtList.append(evt)

if inHeader:
    print("Error -- Can't find column headers", file=sys.stderr)
    sys.exit(1)

with open('TimingLookups.h', 'w+') as outFile:
    # Emit event list lookup
    outFile.write('''/*
 * Machine-generated file -- do not edit!
 */

/* Get list of events for specified mode */
static const unsigned char *
eventListForMode(int mode)
{
    switch (mode) {
''')
    for mode, modeInfo in modeDict.items():
        evtList = modeInfo['events']
        outFile.write('    case %s:{static const unsigned char e[] = {' % (mode))
        for e in evtList:
            outFile.write('%d, ' %(e))
            sep = ', '
        print('127}; return e;}', file=outFile)

    outFile.write('''    default: break;
    }
    return NULL;
}
''')

    # Emit time stamp lookup
    outFile.write('''
static int
getTimestamp(int evtCode, int injFieldSync, int extrFieldSync, int numBunches, int gunBunchesDelay, int targetBucket)
{
    switch (evtCode) {
''')
    for evtCode, evtInfo in eventDict.items():
        outFile.write('    case %d: return %s' % (evtCode, evtInfo[0]))
        if evtInfo[1] != 0:
            outFile.write(' + %d' % (evtInfo[1]))
        if evtInfo[2] > 0:
            outFile.write(' + %d' % (evtInfo[1]))
        elif evtInfo[2] < 0:
            outFile.write(' - %d' % (-evtInfo[2]))
        print(';', file=outFile)
    outFile.write('''    default: break;
    }
    return -1;
}
''')
