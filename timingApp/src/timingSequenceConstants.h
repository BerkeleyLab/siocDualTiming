#ifndef __TIMINGSEQUENCECONSTANTS_H__
#define __TIMINGSEQUENCECONSTANTS_H__

// Array capacities
#define MAX_SEQUENCE_LENGTH   100
#define EVG_SEQUENCE_CAPACITY 200

// Ranges for request parameters
#define MIN_BUCKETS 1
#define MAX_BUCKETS 328
#define MIN_BUNCHES 1
#define MAX_BUNCHES 16

// Delay window (seconds)
#define REQUEST_WINDOW 0.5

// Timeout for awaiting sequence start.
// Assume dead and try again (seconds)
#define TIMEOUT_AWAIT_START 5

// Timeout for awaiting precompletion event.
// Assume dead and try again (seconds)
#define TIMEOUT_AWAIT_PRECOMPLETION 5

// Timeout for awaiting precompletion event.
// Assume dead and try again (seconds)
#define TIMEOUT_AWAIT_LOAD_REQUEST 5

// Special mode
#define SRINJECTION_MODE      40

// Special events
#define GUNON_EVTCODE         36
#define GUNOFF_EVTCODE        37
#define SEQUENCE_END_EVTCODE  127

// Upper limit on allowable beam current (mA)
#define MAX_BEAM_CURRENT        510.0

#endif // __TIMINGSEQUENCECONSTANTS_H__

