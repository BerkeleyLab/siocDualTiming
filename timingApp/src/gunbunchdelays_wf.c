#include <aSubRecord.h>
#include <registryFunction.h>
#include <epicsExport.h>
#include <stdio.h>
#include <epicsTypes.h>

// For extra debugging output (requires a recompile to activate)
#define DBGFLAG 0

// Max # bunches could actually be as high as 16, but for now it's being limited to 4.
// Note that if it's too high the number of inputs/outputs will exceed the aSub
// record capacity.
#define MIN_GUNBUNCHES 1
#define MAX_GUNBUNCHES 4

// Conversion from units of 4*BROC to EvtClkTicks
#define BROCTOTICKS    125
/**
 * gunbunchdelays_wf: aSub record for linking the GunBunchToInjFieldTrigger waveform
 * record to the GunBunchDelay-x (x = 1-4) pvs, plus GunBunchDelay and TimGunBunchCount,
 * so that updating the waveform results in the individual pvs getting updated, while
 * updating the pvs results in the waveform getting updated.
 * Two aSub records are expected:
 * 1. From waveform to delays:
 *		INPA = #Bunches (index into waveform array)
 *		INPB = waveform
 *		OUTA = currently active delay
 *		OUTB = delay1
 *		OUTC = delay2
 *		OUTD = delay3
 *		OUTE = delay4
 * 2. From delays to waveform:
 *		INPA = #Bunches (index into waveform array)
 *		INPB = currently active delay
 *		INPC = delay1
 *		INPD = delay2
 *		INPE = delay3
 *		INPF = delay4
 *		OUTA = waveform
 * The field types for all inputs (FTX) and outputs (FTVx) are assumed to be "LONG"
 *
 * @date Sept. 2017
 * @author Bob Gunion
 */

/* Simple struct to keep track of previous values */
typedef struct {
	epicsInt32 count;
	epicsInt32 delay;
	epicsInt32 delays[MAX_GUNBUNCHES];
} GunBunchDelays;
GunBunchDelays prevVals;

/**
 * Initialization function.  The INAM field of the delays-to-waveform aSub record.
 * Simply copies all values to the prevVals struct.
 */
static long init_gunbunchdelays(aSubRecord *prec) {
	if (DBGFLAG) {
		printf("in init_gunbunchdelays\n");
	}
	prevVals.count = *(epicsInt32 *)prec->a;
	prevVals.delay = *(epicsInt32 *)prec->b;
	prevVals.delays[0] = *(epicsInt32 *)prec->c;
	prevVals.delays[1] = *(epicsInt32 *)prec->d;
	prevVals.delays[2] = *(epicsInt32 *)prec->e;
	prevVals.delays[3] = *(epicsInt32 *)prec->f;

	return 0;
}

/**
 * From wavefunction to delays:
 * Copies the waveform values to the individual delays.  Also copies the currently
 * active delay, using the count to determine the correct index.
 */
static long gunbunchdelay_from_wf(aSubRecord *prec) {
	epicsInt32 *count, *wf, *delay;
	epicsInt32 *delays[MAX_GUNBUNCHES], i;

	if (DBGFLAG) {
		printf("in gunbunchdelay_from_wf\n");
	}
	count = (epicsInt32 *)prec->a;
	wf = (epicsInt32 *)prec->b;
	delay = (epicsInt32 *)prec->vala;
	delays[0] = (epicsInt32 *)prec->valb;
	delays[1] = (epicsInt32 *)prec->valc;
	delays[2] = (epicsInt32 *)prec->vald;
	delays[3] = (epicsInt32 *)prec->vale;
	if (DBGFLAG) {
		printf("gunbunch_from_wf: count = %d;wf1-4 = %d %d %d %d\n", *count, wf[0], wf[1], wf[2], wf[3]);
	}

	if (*count < MIN_GUNBUNCHES || *count > MAX_GUNBUNCHES) {
		// illegal value
		return 1;
	}

	*delay = (wf[(*count)-1])/BROCTOTICKS;
	for (i = 0; i < MAX_GUNBUNCHES; ++i) {
		*(delays[i]) = (wf[i])/BROCTOTICKS;
	}
	if (DBGFLAG) {
		printf("gunbunch_from_wf: result = delay = %d; d1-4 = %d %d %d %d\n", *delay, *(delays[0]), *(delays[1]), *(delays[2]), *(delays[3]));
	}

	return 0;
}

/**
 * From delays to waveform:
 * Copies the individual delays to the waveform.  Also copies the currently
 * active delay if the changed delay matches the gunbunch count.
 */
static long gunbunchdelay_to_wf(aSubRecord *prec) {
	epicsInt32 *count, *delay;
	epicsInt32 delays[MAX_GUNBUNCHES];
	epicsInt32 * wf, i, found;

	if (DBGFLAG) {
		printf("in gunbunchdelay_to_wf\n");
	}
	count = (epicsInt32 *)prec->a; // count
	delay = (epicsInt32 *)prec->b; // wf[count-1]
	delays[0] = *(epicsInt32 *)prec->c;
	delays[1] = *(epicsInt32 *)prec->d;
	delays[2] = *(epicsInt32 *)prec->e;
	delays[3] = *(epicsInt32 *)prec->f;
	if (DBGFLAG) {
		printf("gunbunch_to_wf: count: %d delay: %d d1-4: %d %d %d %d\n", *count, *delay, delays[0], delays[1], delays[2], delays[3]);
	}
	wf = (epicsInt32 *)prec->vala;

	if (*count < MIN_GUNBUNCHES || *count > MAX_GUNBUNCHES) {
		// illegal value
		if (DBGFLAG) {
			printf("illegal value for count: %d\n", *count);
		}
		return 1;
	}

	// Determine which input changed
	if (*count != prevVals.count) {
		if (DBGFLAG) {
			printf("count changed from %d to %d\n" , prevVals.count, *count);
		}
		prevVals.count = *count;
		prevVals.delay = prevVals.delays[(*count)-1];
	}

	if (*delay != prevVals.delay) {
		prevVals.delays[(*count)-1] = *delay;
		prevVals.delay = *delay;
	}
	found = 0;
	for (i = 0; i < MAX_GUNBUNCHES; ++i) {
		if (delays[i] != prevVals.delays[i]) {
			prevVals.delays[i] = delays[i];
			if (*count == (i+1)) {
				prevVals.delay = delays[i];
			}
			found = 1;
		}
	}
	if (!found) {
		if (DBGFLAG) {
			printf("Nothing changed\n");
		}
	}

	for (i = 0; i < MAX_GUNBUNCHES; ++i) {
		wf[i] = BROCTOTICKS*(prevVals.delays[i]);
	}
	if (DBGFLAG) {
		printf("gunbunch_to_wf: wf = %d %d %d %d\n", wf[0], wf[1], wf[2], wf[3]);
	}

	return 0;
}

epicsRegisterFunction(init_gunbunchdelays);
epicsRegisterFunction(gunbunchdelay_from_wf);
epicsRegisterFunction(gunbunchdelay_to_wf);


