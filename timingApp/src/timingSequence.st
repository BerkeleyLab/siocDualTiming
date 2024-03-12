program timingSequence ("T=,P=EVG1:,R=")

// Macros
//  T: Timing system record prefix.
//  P:, R: Event generator record prefixes.
// Defaults provided here can be overridden by seq command in st.cmd.

// No wait for connections
option -c;
// Safe mode
option +s;
// Enable run-time debug messages
option +d;

#include "timingSequenceConstants.h"
%%#include <stdio.h>
%%#include <stdlib.h>

/*
 * Injection request waveform.
 */
int request[7];
assign request to "{T}TimInjReq";
monitor request;
evflag requestFlag;
sync request requestFlag;
unsigned int modeIndexes[255];
%{
typedef enum { /* Request waveform indices. */
        TARGET_BUCKET,
        GUN_BUNCHES,
        INJ_MODE,
        GUN_INHIBIT,
        INJ_FIELD_SYNC_DELAY,
        EXTR_FIELD_SYNC_DELAY,
        SEQUENCE,
} REQUEST_FIELDS;
}%

/* Values extracted from injection request waveform: */
int sequence = 0;   /* Sequence #: request ignored if no change from previous */
int lastSequence = -1;
int bucket = 1;     /* Target bucket (1-328) */
int bunches = 1;    /* Number of electron gun bunches (1-16) */
int inhibit = 0;    /* Inhibit electron gun if set, even if mode allows gun */
int mode = 0;       /* Type of injection sequence.  See eventListForMode() */
int injFieldSync;   /* Injection field delay */
int extrFieldSync;  /* Extraction field delay */

/*
 * Monitor of injection request values sent to FPGA sequencer.
 */

int sequenceMon = 0;   /* Sequence #: request ignored if no change from previous */
assign sequenceMon to "${T}TimSequenceNumberMon";
int bucketMon = 1;     /* Target bucket (1-328) */
assign bucketMon to "$(T)TimTargetBucketMon";
int bunchesMon = 1;    /* Number of electron gun bunches (1-16) */
assign bunchesMon to "$(T)TimGunBunchCountMon";
int inhibitMon = 0;    /* Inhibit electron gun if set, even if mode allows gun */
assign inhibitMon to "$(T)TimGunInhibitMon";
int modeMon = 0;       /* Type of injection sequence.  See eventListForMode() */
assign modeMon to "$(T)TimInjModeMon";
int injFieldSyncMon;   /* Injection field delay */
assign injFieldSyncMon to "$(T)TimInjFieldSyncDelayMon";
int extrFieldSyncMon;  /* Extraction field delay */
assign extrFieldSyncMon to "$(T)TimExtrFieldSyncDelayMon";

/*
 * Storage ring current.
 * Sequencer refuses to inject when this exceeds MAX_BEAM_CURRENT.
 */
double beamcurrent;
assign beamcurrent to "SR:DCCT:AVG";
monitor beamcurrent;

/*
 * Overall timing system enable/disable
 */
int potentate;
assign potentate to "{T}TimPotentate";
monitor potentate;
int injCycleEnable;
assign injCycleEnable to "{P}{R}INJ:injCycleEnable";


/*
 * Statistics
 */
%{
typedef enum {
    FC_SUCCESS,
    FC_MISSING_CONNECTION,
    FC_START_OVERRUN,
    FC_STALE_SEQUENCE,
    FC_INVALID_MODE,
    FC_INVALID_BUCKET,
    FC_INVALID_BUNCHES,
    FC_INVALID_BEAM_CURRENT,
    FC_EXCESSIVE_BEAM_CURRENT,
    FC_PV_SEVERITY,
    FC_BAD_EVR,
    FC_NO_EOS,
} FAULT_CODE;
}%
int goodCount;
assign goodCount to "{T}InjSeqSuccessCount";
int badCount;
assign badCount to "{T}InjSeqFailedCount";
int faultCode;
assign faultCode to "{T}InjSeqFaultCode";
int duplicateTimestampFound;
assign duplicateTimestampFound to "{T}InjSeqDupTimestamp";
int startOverrunCount;
assign startOverrunCount to "{T}InjSeqStartOverrunCount";

/*
 * Diagnostics
 */
int debugFlag;
assign debugFlag to "{T}InjSeqDebug";
monitor debugFlag;

/**
 * Mapping of # gun bunches to injection field trigger
 */
double bunchesToField[MAX_BUNCHES];
assign bunchesToField to "{T}GunBunchToInjFieldTrigger";
monitor bunchesToField;
int gunBunchesDelay;

/*
 * Injection cycles are initiated only when all EVR links are good.
 */
int allEVRvalid;
assign allEVRvalid to "{T}TimAllEVRvalid";
monitor allEVRvalid;

/*
 * Event generator FPGA
 */
#define EVG_SEQ_STATUS_ACTIVE 0x8
#define EVG_SEQ_STATUS_BUSY   0x10
int evgSequence[EVG_SEQUENCE_CAPACITY];
assign evgSequence to "{P}{R}E1:SEQ1";
int evgSeqEnable;
assign evgSeqEnable to "{P}{R}E1:SEQ1:enable";
int evgSeqStatus;
assign evgSeqStatus to "{P}{R}E1:seqStatus";
monitor evgSeqStatus;
int evgSequencerStarts;
assign evgSequencerStarts to "{P}{R}E1:seqStarts";
monitor evgSequencerStarts;
int evgSequencerCurrentStarts;

%{
/*
 * Comparison routine for qsort
 * Primary sort on time stamp (first word)
 * Secondary sort on event code (second word)
 */
static int
tsCompare(const void *a, const void *b)
{
    const int *ap = a, *bp = b;
    int diff;
    if ((diff = ap[0] - bp[0]) == 0) {
        diff = ap[1] - bp[1];
    }
    return diff;
}

/*
 * Ensure monotonically increasing time stamps
 * and convert time stamps to delay.
 */
static int
monotonicSequence(int count, int *tstampsAndEvents)
{
    int i, idx;
    int ret = 1;
    int prev = -1;
    for (i = 0, idx = 0; i < count; i++, idx += 2) {
        int this = tstampsAndEvents[idx];
        if ((i < (count - 1)) && (tstampsAndEvents[idx+2] <= this)) {
            ret = 0;
            tstampsAndEvents[idx+2] = this + 1;
        }
        tstampsAndEvents[idx] = (this - prev) - 1;
        prev = this;
    }
    return ret;
}

#define END_OF_SEQUENCE_TICKS (1<<30)
#include "TimingLookups.h"

}%

ss ssTiming {
    /*
     * Initial state
     * Set up some stuff
     */
    state start {
        when() {
            duplicateTimestampFound = 0;
            pvPut(duplicateTimestampFound);
        } state await_connections
    }

    /*
     * Wait for connections to complete
     */
    state await_connections {
        int oldConnectCount;
        entry {
            if(debugFlag) printf("State: await_connections\n");
            oldConnectCount = -1;
        }
        when (pvConnectCount() == pvAssignCount()) {
            if (faultCode == FC_MISSING_CONNECTION) {
                faultCode = FC_SUCCESS;
                pvPut(faultCode);
            }
        } state await_potentate
        when (delay(10) && (pvConnectCount() != oldConnectCount)) {
            oldConnectCount = pvConnectCount();
            printf("Timing Sequencer: %d/%d connected\n", pvConnectCount(),
                                                          pvAssignCount());
            if (faultCode == FC_SUCCESS) {
                faultCode = FC_MISSING_CONNECTION;
                pvPut(faultCode);
            }
        } state await_connections
    }

    /*
     * Wait for injection cycles to be enabled
     */
    state await_potentate {
        entry {
            if(debugFlag) printf("State: await_potentate\n");
        }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate != 0) {
            injCycleEnable = 1;
            pvPut(injCycleEnable, SYNC);
        } state sync_await_start
    }

    /*
     * Initial synchronization
     */
    state sync_await_start {
        entry { if(debugFlag) printf("State: sync_await_start\n"); }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate == 0) { } state no_potentate
        when ((evgSeqStatus & EVG_SEQ_STATUS_ACTIVE) != 0) {
        } state await_completion
    }

    /*
     * Wait for injection cycle to complete
     */
    state await_completion {
        entry { if(debugFlag) printf("State: await_completion\n"); }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate == 0) { } state no_potentate
        when ((evgSeqStatus & EVG_SEQ_STATUS_ACTIVE) == 0) { } state await_start
    }

    /*
     * Wait for injection cycle to start
     */
    state await_start {
        entry { if(debugFlag) printf("State: await_start\n"); }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate == 0) { } state no_potentate
        when ((evgSeqStatus & EVG_SEQ_STATUS_ACTIVE) != 0) {
                                                    } state await_precompletion
    }

    /*
     * Wait for injection cycle to reach precompletion point
     */
    state await_precompletion {
        entry { if(debugFlag) printf("State: await_precompletion\n"); }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate == 0) { } state no_potentate
        when (efTestAndClear(requestFlag)) {
            /* Ignore requests outside expected window */
        } state await_precompletion

        when ((evgSeqStatus & EVG_SEQ_STATUS_BUSY) == 0) {
            evgSequencerCurrentStarts = evgSequencerStarts;
        } state await_request
    }

    /*
     * Watch for injection request
     */
    state await_request {
        entry { if(debugFlag) printf("State: await_request\n"); }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate == 0) { } state no_potentate
        when (delay(REQUEST_WINDOW)) {
            /* No request, default cycle will be emitted */
        } state await_completion

        when (evgSequencerStarts != evgSequencerCurrentStarts) {
            faultCode = FC_START_OVERRUN;
            startOverrunCount++;
            pvPut(startOverrunCount);
        } state increment_bad_count

        when (efTestAndClear(requestFlag)) {
            if (sequence == request[SEQUENCE]) {
                /* No request, or perhaps it was truncated */
                state await_completion;
            }
            bucket   = request[TARGET_BUCKET];
            bunches  = request[GUN_BUNCHES];
            mode     = request[INJ_MODE];
            inhibit  = request[GUN_INHIBIT];
            sequence = request[SEQUENCE];
            injFieldSync = request[INJ_FIELD_SYNC_DELAY];
            extrFieldSync = request[EXTR_FIELD_SYNC_DELAY];
        } state validate_request
    }

    /*
     * Transient sequential states to validate, prepare, and send sequence
     */
    state validate_request {
        entry { if(debugFlag) printf("State: validate_request\n"); }
        when (sequence == lastSequence) {
            faultCode = FC_STALE_SEQUENCE;
        } state increment_bad_count

        when ((bucket < MIN_BUCKETS) || (bucket > MAX_BUCKETS)) {
            faultCode = FC_INVALID_BUCKET;
        } state increment_bad_count

        when ((bunches < MIN_BUNCHES) || (bunches > MAX_BUNCHES)) {
            faultCode = FC_INVALID_BUNCHES;
        } state increment_bad_count

        when () {
        } state check_beamcurrent
    }

    state check_beamcurrent {
        entry { if(debugFlag) printf("State: check_beamcurrent\n"); }
        when ((mode == SRINJECTION_MODE) && (pvSeverity(beamcurrent) == pvSevrINVALID)) {
            faultCode = FC_INVALID_BEAM_CURRENT;
        } state increment_bad_count

        when ((mode == SRINJECTION_MODE) && (beamcurrent > MAX_BEAM_CURRENT)) {
            faultCode = FC_EXCESSIVE_BEAM_CURRENT;
        } state increment_bad_count

        when () {
        } state check_severities
    }

    state check_severities {
        entry { if(debugFlag) printf("State: check_severities\n"); }
        when ((pvSeverity(evgSeqStatus) != pvSevrNONE)
            || (pvSeverity(evgSequencerStarts) != pvSevrNONE)) {
            faultCode = FC_PV_SEVERITY;
        } state increment_bad_count

        when () {
        } state check_links
    }

    state check_links {
        entry { if(debugFlag) printf("State: check_links\n"); }
        when ((pvStatus(allEVRvalid) != pvStatOK) || (allEVRvalid == 0)) {
            faultCode = FC_BAD_EVR;
        } state increment_bad_count

        when () {
        } state create_requested_sequence
    }

    /*
     * Create the new sequence
     */
    state create_requested_sequence {
        entry { if(debugFlag) printf("State: create_requested_sequence\n"); }
        when () {
            %%const unsigned char *e;
            int targetBucketDelay = (125 * ((bucket * 21) % 328)) / 4;
            int i, nTStamps;
            int highwater = 0;
            int foundEOS = 0;

            /*
             * Get time stamp for each event and merge into common array
             */
            e = eventListForMode(mode);
            if (e == NULL) {
                faultCode = FC_INVALID_MODE;
                state increment_bad_count;
            }
            gunBunchesDelay = bunchesToField[bunches-1];
            for (i = 0, nTStamps = 0; i < MAX_SEQUENCE_LENGTH; i++) {
                int event = e[i];
                int tstamp;
                if (inhibit) {
                    if (event == GUNON_EVTCODE || event == GUNOFF_EVTCODE) {
                        continue;
                    }
                }
                if (event == SEQUENCE_END_EVTCODE) {
                    tstamp = highwater;
                }
                else {
                    tstamp = getTimestamp(event, injFieldSync, extrFieldSync,
                                   bunches, gunBunchesDelay, targetBucketDelay);
                    if (tstamp > (END_OF_SEQUENCE_TICKS / 2)) {
                        tstamp = highwater + (tstamp - END_OF_SEQUENCE_TICKS) + 2;
                    }
                    if (tstamp < 0) {
                        fprintf(stderr, "WARNING: tstamp for evtcode %d is %d"
                                               " -- ignoring\n", event, tstamp);
                        continue;
                    }
                    if (tstamp >= highwater) {
                        highwater = tstamp + 1;
                    }
                }
                evgSequence[(2*nTStamps)+0] = tstamp;
                evgSequence[(2*nTStamps)+1] = event;
                nTStamps++;
                if (event == SEQUENCE_END_EVTCODE) {
                    foundEOS = 1;
                    break;
                }
            }
            if (!foundEOS) {
                faultCode = FC_NO_EOS;
                state increment_bad_count;
            }
            qsort(evgSequence, nTStamps, 2*sizeof(int), tsCompare);
            if (!monotonicSequence(nTStamps, evgSequence)) {
                duplicateTimestampFound = 1;
                pvPut(duplicateTimestampFound);
            }
        } state load_requested_sequence
    }

    state load_requested_sequence {
        entry {
            if(debugFlag) {
                printf("State: load_requested_sequence\n");
                if(debugFlag >= 2) {
                    int i;
                    for (i = 0 ; i < 7 ; i++) {
                        printf(" %d", request[i]);
                    }
                    printf("\n");
                }
            }
        }
        when (pvConnectCount() != pvAssignCount()) { } state missing_connection
        when (potentate == 0) { } state no_potentate
        when (evgSequencerStarts != evgSequencerCurrentStarts) {
            faultCode = FC_START_OVERRUN;
            startOverrunCount++;
            pvPut(startOverrunCount);
        } state increment_bad_count

        when ((evgSeqStatus & EVG_SEQ_STATUS_ACTIVE) == 0) {
            pvPut(evgSequence);
            evgSeqEnable = 1;
            pvPut(evgSeqEnable);
            lastSequence = sequence;
            faultCode = FC_SUCCESS;
            pvPut(faultCode);
            goodCount++;
            pvPut(goodCount);

            /* assign monitor values to injection parameters */
            sequenceMon = sequence;
            pvPut(sequenceMon);
            bucketMon = bucket;
            pvPut(bucketMon);
            bunchesMon = bunches;
            pvPut(bunchesMon);
            inhibitMon = inhibit;
            pvPut(inhibitMon);
            modeMon = mode;
            pvPut(modeMon);
            injFieldSyncMon = injFieldSync;
            pvPut(injFieldSyncMon);
            extrFieldSyncMon = extrFieldSync;
            pvPut(extrFieldSyncMon);
        } state await_start
    }

    state no_potentate {
        when() {
            injCycleEnable = 0;
            pvPut(injCycleEnable, SYNC);
        } state await_potentate
    }

    state missing_connection {
        when() {
            faultCode = FC_MISSING_CONNECTION;
            pvPut(faultCode);
            injCycleEnable = 0;
            pvPut(injCycleEnable, SYNC);
        } state await_connections
    }

    state increment_bad_count {
        entry { if(debugFlag) printf("State: increment_bad_count\n"); }
        when() {
            pvPut(faultCode);
            badCount++;
            pvPut(badCount);
        } state await_completion
    }
}
