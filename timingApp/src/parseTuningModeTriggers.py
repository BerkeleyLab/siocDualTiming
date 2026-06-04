#!/usr/bin/env python

import csv
import sys
import re

from collections import defaultdict

EventColumn = -1
OffsetColumn = -1
CategoryColumn = -1
TickOffsetColumn = -1

modeDict = {}
modeCategoryDict = {}
modeFuncTimeDict = {}

duplicateCheckDict = defaultdict(dict)
consistencyCheckDict = defaultdict(dict)


def checkForDuplicates(mode, evt, signature, checkDict, lineno):
    if mode in checkDict and signature in checkDict[mode]:
        duplicateEvent = checkDict[mode][signature]

        if evt != duplicateEvent:
            print(
                f"Line {lineno} -- Event {evt} is identical to event {duplicateEvent} for mode {mode}"
            )
            print(f"signature -- {signature}")
            return True
    else:
        checkDict[mode][signature] = evt

    return False


def checkForInconsistency(mode, evt, signature, checkDict, lineno):
    if mode in checkDict and evt in checkDict[mode]:
        matchSignature = checkDict[mode][evt]
        if signature != matchSignature:
            print(
                f"Line {lineno} -- Event {evt} has different conditions/actions for mode {mode}"
            )
            print(f"signature -- {signature}")
            return True
    else:
        checkDict[mode][evt] = signature

    return False


def match(pattern, string):
    return re.match(pattern, string, re.IGNORECASE)


def search(pattern, string):
    return re.search(pattern, string, re.IGNORECASE)


def locationInList(pattern, l):
    return next((i for i, item in enumerate(l) if search(pattern, item)), None)


def offset(expr, str, lineno):
    if match(r"^[\s]*[-]?[\d]+[\s]*$", str):
        n = int(str)
        if n < 0:
            return expr + " - %d" % (-n)
        if n > 0:
            return expr + " + %d" % (n)
    elif not match(r"^[\s]*$", str):
        print(f'Line {lineno} -- Error: Bad offset "{str}"', file=sys.stderr)
        sys.exit(1)
    return expr


with open("TuningModeTriggers.csv") as csvFile:
    reader = csv.reader(csvFile)
    lineno = 0
    inHeader = True
    modeNumberFound = False
    modeNumberDone = False
    funcTimeModeNumberFound = False
    funcTimeModeNumberDone = False
    catModeNumberFound = False
    catModeNumberDone = False
    for line in reader:
        lineno += 1
        if inHeader:

            ########################################
            # Look for Functional "Mode Number"
            ########################################
            if not modeNumberFound:
                loc = locationInList(r"Mode[\s]Number", line)
                if loc is None or loc != 0:
                    continue
                else:
                    modeNumberFound = True

            for c in range(0, len(line)):
                if modeNumberDone:
                    break

                val = line[c]
                if match(r"[\d]+", val):
                    if val in modeDict:
                        print(f"Column {c} -- Duplicate mode number {val}")
                        sys.exit(1)
                    modeDict[val] = {"column": c, "events": []}
                if match(r"Number", val):
                    EventColumn = c
                if match(r"Timestamp[\s]Offset", val):
                    OffsetColumn = c
                if match(r"Offset[\s]\[Ticks\]", val):
                    TickOffsetColumn = c
                    modeNumberDone = True

            if (
                EventColumn < 0
                or OffsetColumn < 0
                or TickOffsetColumn < 0
                or len(modeDict) == 0
                or not modeNumberDone
            ):
                print(
                    f"Line {lineno} -- Error: Bad heading (mode number)",
                    file=sys.stderr,
                )
                sys.exit(1)

            ########################################
            # Look for "Functional Time Mode Number"
            ########################################
            if not funcTimeModeNumberFound:
                loc = locationInList(r"Functional[\s]Time[\s]Mode[\s]Number", line)
                if loc is None:
                    continue
                else:
                    funcTimeModeNumberFound = True

            for c in range(loc + 1, len(line)):
                if funcTimeModeNumberDone:
                    break

                val = line[c]
                if match(r"[\d]+", val):
                    if val in modeFuncTimeDict:
                        print(
                            f"Column {c + 1} -- Duplicate functional time mode number {val}"
                        )
                        sys.exit(1)
                    modeFuncTimeDict[val] = {"column": c}
                else:
                    funcTimeModeNumberDone = True

            if len(modeFuncTimeDict) == 0 or not funcTimeModeNumberDone:
                print(
                    f"Line {lineno} -- Error: Bad heading (functional time mode)",
                    file=sys.stderr,
                )
                sys.exit(1)

            ########################################
            # Look for "Category Mode Number"
            ########################################
            if not catModeNumberFound:
                loc = locationInList(r"Category[\s]Mode[\s]Number", line)
                if loc is None:
                    continue
                else:
                    catModeNumberFound = True

            for c in range(loc + 1, len(line)):
                if catModeNumberDone:
                    break

                val = line[c]
                if match(r"[\d]+", val):
                    if val in modeCategoryDict:
                        print(f"Column {c + 1} -- Duplicate category mode number {val}")
                        sys.exit(1)
                    modeCategoryDict[val] = {"column": c}
                else:
                    catModeNumberDone = True

            if len(modeCategoryDict) == 0:
                print(
                    f"Line {lineno} -- Error: Bad heading (category mode)",
                    file=sys.stderr,
                )
                sys.exit(1)

            inHeader = False
        else:
            evt = line[EventColumn]
            if match(r"^[\s]*[\d]+[\s]*$", evt):
                evt = int(evt)
                if evt == 127:
                    break
                if evt <= 0 or evt > 255:
                    print(
                        f"Line {lineno} -- Error: Bad event number {evt}",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                # Note modes for which event is active
                for mode, modeInfo in modeDict.items():
                    col = modeInfo["column"]
                    isActive = line[col]
                    if match(r"^[\s]*x[\s]*$", isActive):
                        evtList = modeInfo["events"]

                        # Check if we have a functional time column defined for
                        # this mode
                        if modeFuncTimeDict[mode] is None:
                            print(
                                f"No Functional Time Mode number for mode {mode}",
                                file=sys.stderr,
                            )
                            sys.exit(1)

                        exprCol = modeFuncTimeDict[mode]["column"]
                        exprStr = line[exprCol]

                        # Canonicalize expression
                        if match(r"^[\s]*$", exprStr) or match(
                            r"^[\s]*Start[\s]*$", exprStr
                        ):
                            exprStr = "0"
                        elif match(r"^[\s]*End", exprStr):
                            exprStr = "END_OF_SEQUENCE_TICKS"
                        else:
                            exprStr = re.sub(
                                r"InjFieldSync", "injFieldSync", exprStr, re.IGNORECASE
                            )
                            exprStr = re.sub(
                                r"GunBunchDelay",
                                "gunBunchesDelay",
                                exprStr,
                                re.IGNORECASE,
                            )
                            exprStr = re.sub(
                                r"#[\s]*Bunches", "numBunches", exprStr, re.IGNORECASE
                            )
                            exprStr = re.sub(
                                r"ExtrFieldSync",
                                "extrFieldSync",
                                exprStr,
                                re.IGNORECASE,
                            )
                            exprStr = re.sub(
                                r"TargetBucket",
                                "targetBucketDelay",
                                exprStr,
                                re.IGNORECASE,
                            )
                            exprStr = re.sub(r"[\s]+", "", exprStr)
                            exprStr = re.sub(r"\+", " + ", exprStr)
                        exprStr = offset(exprStr, line[TickOffsetColumn], lineno)
                        exprStr = offset(exprStr, line[OffsetColumn], lineno)
                        signature = exprStr
                        tstamp = exprStr

                        # Check if we have a category column defined for
                        # this mode
                        if modeCategoryDict[mode] is None:
                            print(
                                f"No Category Mode number for mode {mode}",
                                file=sys.stderr,
                            )
                            sys.exit(1)

                        catCol = modeCategoryDict[mode]["column"]
                        catStr = line[catCol]
                        cat = 0

                        if match(r"^[\s]*[\d]+[\s]*$", catStr):
                            cat = int(catStr)
                            if cat < 0 or cat > 255:
                                print(
                                    f"Line {lineno} -- Error: Bad category number {cat}",
                                    file=sys.stderr,
                                )
                                sys.exit(1)
                        elif not match(r"^[\s]*$", catStr):
                            print(
                                f"Line {lineno} -- Error: Bad 'active event' value in column {col + 1}",
                                file=sys.stderr,
                            )
                            sys.exit(1)

                        if not any(evtItem.get("number") == evt for evtItem in evtList):
                            newEvt = {"number": evt, "tstamp": tstamp, "cat": cat}
                            evtList.append(newEvt)

                        checkForDuplicates(
                            mode, evt, signature, duplicateCheckDict, lineno
                        )
                        fail = checkForInconsistency(
                            mode, evt, signature, consistencyCheckDict, lineno
                        )
                        if fail:
                            sys.exit(1)

                    elif not match(r"^[\s]*$", isActive):
                        print(
                            f"Line {lineno} -- Error: Bad 'active event' value in column {col + 1}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

if inHeader:
    # Header must have been fully processed
    if not modeNumberFound:
        print(
            f'Error: "Mode Number" was not found in header',
            file=sys.stderr,
        )
        sys.exit(1)

    if not funcTimeModeNumberFound:
        print(
            f'Error: "Functional Time Mode Number" was not found in header',
            file=sys.stderr,
        )
        sys.exit(1)

    if not catModeNumberFound:
        print(
            f'Error: "Category Mode Number" was not found in header',
            file=sys.stderr,
        )
        sys.exit(1)

with open("TimingLookups.h", "w+") as outFile:
    # Emit event list lookup
    outFile.write(
        """/*
 * Machine-generated file -- do not edit!
 */

static const unsigned char *
eventListForMode(int mode)
{
    switch (mode) {
"""
    )
    for mode, modeInfo in modeDict.items():
        evtList = modeInfo["events"]
        outFile.write(f"    case {mode}: {{ static const unsigned char e[] = {{ ")
        for e in evtList:
            outFile.write(f"{e['number']}, ")
        print("127 }; return e;}", file=outFile)

    outFile.write(
        """    default: break;
    }
    return NULL;
}
"""
    )

    # Emit time stamp lookup
    outFile.write(
        """
static int
getTimestamp(int mode, int evtCode, int injFieldSync, int extrFieldSync, int numBunches, int gunBunchesDelay, int targetBucketDelay)
{
    switch (mode) {
"""
    )
    for mode, modeInfo in modeDict.items():
        evtList = modeInfo["events"]
        print(f"    case {mode}:", file=outFile)
        print(f"        switch (evtCode) {{", file=outFile)

        for e in evtList:
            print(f"        case {e['number']}: return {e['tstamp']};", file=outFile)
        outFile.write(
            """        default: return -1;
        }
"""
        )
        print("        break;", file=outFile)
    outFile.write(
        """    default: break;

    }
    return -1;
}
"""
    )

    # Emit category lookup
    outFile.write(
        """
static int
getCategory(int mode, int evtCode)
{
    switch (mode) {
"""
    )
    for mode, modeInfo in modeDict.items():
        evtList = modeInfo["events"]
        print(f"    case {mode}:", file=outFile)
        print(f"        switch (evtCode) {{", file=outFile)

        for e in evtList:
            print(f"        case {e['number']}: return {e['cat']};", file=outFile)
        outFile.write(
            """        default: return -1;
        }
"""
        )
        print("        break;", file=outFile)
    outFile.write(
        """    default: break;

    }
    return -1;
}
"""
    )
