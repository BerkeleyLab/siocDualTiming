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
duplicateCheckDict = { }
consistencyCheckDict = { }

def match(pattern, string):
    return re.match(pattern, string, re.IGNORECASE)

def offset(expr, str, lineno):
    if match('^[\s]*[-]?[\d]+[\s]*$', str):
        n = int(str)
        if (n < 0):
            return (expr + ' - %d' % (-n))
        if (n > 0):
            return (expr + ' + %d' % (n))
    elif not match('^[\s]*$', str):
        print('Line %d -- Error: Bad offset "%s"' % (lineno, str), file=sys.stderr)
        sys.exit(1)
    return expr

with open('TuningModeTriggers.csv') as csvFile:
    reader = csv.reader(csvFile)
    lineno = 0
    inHeader = True
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
                if EventColumn < 0 \
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
                # Canonicalize expression
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
                    expr = re.sub('TargetBucket', 'targetBucketDelay', expr, re.IGNORECASE)
                    expr = re.sub('[\s]+', '', expr)
                    expr = re.sub('\+', ' + ', expr)
                expr = offset(expr, line[TickOffsetColumn], lineno)
                signature = expr
                expr = offset(expr, line[OffsetColumn], lineno)
                # Stash info
                eventDict[evt] = expr
                # Note modes for which event is active
                for mode, modeInfo in modeDict.items():
                    col = modeInfo['column']
                    isActive = line[col]
                    if match('^[\s]*x[\s]*$', isActive):
                        signature = 'x' + signature
                        evtList = modeInfo['events']
                        if not evt in evtList:
                            evtList.append(evt)
                    elif not match('^[\s]*$', isActive):
                        print("Line %d -- Error: Bad value in column %d" % (lineno, col+1), file=sys.stderr)
                        sys.exit(1)
                    else:
                        signature = ' ' + signature
                # Check for duplicates
                if signature in duplicateCheckDict:
                    duplicateEvent = duplicateCheckDict[signature]
                    if evt != duplicateEvent:
                        print("Line %d -- Event %d is identical to event %d" % (lineno, evt, duplicateEvent))
                else:
                    duplicateCheckDict[signature] = evt
                # Check consistency
                if evt in consistencyCheckDict:
                    matchSignature = consistencyCheckDict[evt]
                    if signature != matchSignature:
                        print("Line %d -- Event %d has different conditions/actions" % (lineno, evt))
                        sys.exit(1)
                else:
                    consistencyCheckDict[evt] = signature

if inHeader:
    print("Error -- Can't find column headers", file=sys.stderr)
    sys.exit(1)

with open('TimingLookups.h', 'w+') as outFile:
    # Emit event list lookup
    outFile.write('''/*
 * Machine-generated file -- do not edit!
 */

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
        print('127}; return e;}', file=outFile)

    outFile.write('''    default: break;
    }
    return NULL;
}
''')

    # Emit time stamp lookup
    outFile.write('''
static int
getTimestamp(int evtCode, int injFieldSync, int extrFieldSync, int numBunches, int gunBunchesDelay, int targetBucketDelay)
{
    switch (evtCode) {
''')
    for evtCode, expr in eventDict.items():
        print('    case %d: return %s;' % (evtCode, expr), file=outFile)
    outFile.write('''    default: break;
    }
    return -1;
}
''')
