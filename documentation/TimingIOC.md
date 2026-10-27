# Dual Timing IOC

> [!NOTE]
> **siocDualTiming docs:** [Overview](README.md) · [Timing IOC](TimingIOC.md)<br>
> **Related projects:** [EPICS support module ↗](https://git.als.lbl.gov/accelerator-controls/epics/iocs/DualEventGeneratorSupport/-/blob/HEAD/documentation/EPICSnotes.md) · [Hardware ↗](https://gitlab.lbl.gov/alsu-instrumentation/dual-evg/-/blob/HEAD/documentation/Hardware.md) · [Firmware ↗](https://gitlab.lbl.gov/alsu-instrumentation/dual-evg/-/blob/HEAD/documentation/Firmware.md)

The dual timing IOC (`siocDualTiming`) adds a state notation language (SNL) program around the [event generator support module](https://git.als.lbl.gov/accelerator-controls/epics/iocs/DualEventGeneratorSupport/-/blob/HEAD/documentation/EPICSnotes.md) to build and send injection sequences. It loads the full event generator database, so one IOC both talks to the FPGA and runs the sequencer.

## Contents

- [Record Prefixes](#record-prefixes)
- [Injection Requests](#injection-requests)
- [Timing Records](#timing-records)
- [Event Generator Records Used](#event-generator-records-used)
- [External Records Used](#external-records-used)
- [Operation](#operation)
- [Fault Codes](#fault-codes)
- [AR/SR Swap-out](#arsr-swap-out)
- [IOC Instances](#ioc-instances)
- [Operator Screens and Scripts](#operator-screens-and-scripts)

---

## Record Prefixes

| Macro | Meaning |
|---|---|
| `$(T)` | Timing record prefix. Empty for production, `test` (or `arTest`) for test instances. Set from the `DUAL_TIMING_IOC_TEST` environment variable. |
| `$(P)$(R)` | Event generator record prefix. The startup scripts set `P=$(T)EVG:` and `R=` (empty), so event generator records are `$(T)EVG:…` |

Timing records below are shown with their `$(T)` prefix omitted.

---

## Injection Requests

A client requests an injection cycle by writing the **`TimInjReq`** waveform (7 `LONG` elements):

| Index | Meaning | Range |
|:---:|---|---|
| 0 | Target SR bucket | 1–328 |
| 1 | Number of gun bunches | 1–16 |
| 2 | Injection mode (see below) | |
| 3 | Gun inhibit — 1 drops the gun-on/gun-off events (36/37) | 0/1 |
| 4 | Target AR bucket | 1–304 |
| 5 | Reserved | 0 |
| 6 | Sequence number — must change for each new request. A request with the same number as the previous one is treated as no request (a default cycle is sent). | |

A new request must arrive in time for each injection cycle. If none arrives, a **default** (mode 0) cycle is generated instead.

### Injection modes

| Value | Mode |
|--:|---|
| 0 | Default |
| 10 | Linac Tuning |
| 20 | BR Tuning |
| 30 | BTS Tuning |
| 40 | SR Injection |
| 41 | SR Injection Prep |
| 42 | SR Tuning |
| 50 | Top-off Interlock Test |
| 60 | AR Injection |

The events, timing, and categories for each mode come from `TuningModeTriggers.csv`, converted at build time by `parseTuningModeTriggers.py`. The mode also selects the [injection alignment](https://git.als.lbl.gov/accelerator-controls/epics/iocs/DualEventGeneratorSupport/-/blob/HEAD/documentation/EPICSnotes.md#injection-alignment-records) and synchronization mode written to the event generator.

### Building a request from individual records

For compatibility with existing applications, the request can also be assembled from individual records:

| Record | Element |
|---|---|
| `TimTargetBucket` | SR bucket (longout, 1–328) |
| `TimGunBunchCount` | Gun bunches (longout, 1–16) |
| `TimInjMode` | Injection mode (mbbo, values as above) |
| `TimGunInhibit` | Gun inhibit (bo) |
| `TimTargetARBucket` | AR bucket (alias of `$(P)$(R)INJ:tgtARBucket`) |
| `TimSequenceNumber` | Sequence number (longout) |

Writing `TimInjReqCommit` assembles them into `TimInjReq`. In the other direction, every write to `TimInjReq` is split back into these records, and `TimInjReqRbk` and `TimInjReqTime` show the last request and its time.

---

## Timing Records

| Name | Type | Description |
|---|---|---|
| `TimPotentate` | bi | Global enable/disable for injection cycles. When it is 0, the sequencer stops requesting cycles and holds `INJ:injCycleEnable` at 0. Starts enabled. |
| `TimInjReq` | waveform | [Injection request](#injection-requests), 7 elements. |
| `GunBunchToInjFieldTrigger` | waveform | 16 values, indexed by the number of gun bunches minus one. The selected value adjusts the gun-on and gun-off event delays. Autosaved. Also editable through `GunBunchDelay`… records. |
| `TimCycleDelay` | ao | Additional delay (0–15 s, 8 ns steps) before the end-of-sequence event. |
| `TimAllEVRvalid` | calc | 1 when the monitored event receivers (`B0215:EVR1`, `S0123:EVR1`, `S0817:EVR1`) report valid links. A requested cycle is sent only when this is 1. |
| `InjSeqDebug` | longout | Sequencer diagnostic message level. 1 prints state transitions; 2 also prints each request. |
| `InjSeqSuccessCount` | longout | Incremented for each injection cycle successfully sent. |
| `InjSeqFailedCount` | longout | Incremented for each request that was rejected. |
| `InjSeqFaultCode` | mbbo | Result of the most recent request. See [Fault Codes](#fault-codes). |
| `InjSeqStartOverrunCount` | longout | Incremented each time a sequence started before the program could load the next one. |
| `InjSeqDupTimestamp` | bo | Set when a sequence had two or more events with the same time stamp (later events are moved one tick later). Cleared only by a client. |

### Monitor and support records

The sequencer also writes:

- **Accepted request values:** `TimSequenceNumberMon`, `TimTargetBucketMon`, `TimTargetARBucketMon`, `TimGunBunchCountMon`, `TimGunInhibitMon`, `TimInjModeMon`, and the field-sync delay monitors.
- **Booster targeting:** `TimTgtBRBucket`, `TimTgtBRDelayOffset`, and the booster extraction delay records `B0215:TimSeqFineDelay`, `B0215:TimSeqRemainder`, and `B0215:EVR1-Out:UDC0:Delay-SP`.
- **Aliases to event generator records:** `TimInjAlignSel` (`INJ:alignSel`), `TimInjSyncMode` (`INJ:syncMode`), and `TimTargetARBucket` (`INJ:tgtARBucket`).

---

## Event Generator Records Used

| Record | Use |
|---|---|
| `$(P)$(R)E1:SEQ1` | Receives each generated injection sequence |
| `$(P)$(R)E1:SEQ1:enable` | Enabled after each sequence is written |
| `$(P)$(R)INJ:singleShot` | Triggers each injection cycle |
| `$(P)$(R)INJ:injCycleEnable` | Held at 0 — the sequencer runs in single-shot mode only |
| `$(P)$(R)E1:seqStatus` | Sequencer *active* and *busy* bits |
| `$(P)$(R)E1:seqStarts` | Detects sequence starts and overruns |
| `$(P)$(R)INJ:stBRBucket` | Current target BR bucket |
| `$(P)$(R)INJ:tgtARBucket`, `INJ:alignSel`, `INJ:syncMode` | Written for each cycle (through their `Tim…` aliases) |

> [!NOTE]
> The IOC puts `$(P)$(R)E1:SEQ0` into simulation mode at startup so the FPGA's default sequence (loaded from flash) can't be overwritten by accident.

## External Records Used

| Record | Use |
|---|---|
| `SR:DCCT:AVG` | Storage ring beam current. In **SR Injection** mode (40), a request is rejected if this is INVALID or above **510 mA**. |
| `B0215:EVR1:Link-Sts`, `S0123:EVR1:Link-Sts`, `S0817:EVR1:Link-Sts` | Inputs to `TimAllEVRvalid`. |
| `irm:150:CounterValue`, `irm:151:CounterValue` | Filtered into `TimInjFieldCounterFiltd` and `TimExtrFieldCounterFiltd`. |

---

## Operation

```mermaid
stateDiagram-v2
    [*] --> AwaitConnections: set INJ:injCycleEnable = 0
    AwaitConnections --> AwaitPotentate: all PVs connected
    AwaitPotentate --> AwaitPrecompletion: TimPotentate set
    AwaitPrecompletion --> AwaitRequest: EVG sequence no longer busy
    AwaitPrecompletion --> Default: timeout (5 s)
    AwaitRequest --> Validate: TimInjReq received
    AwaitRequest --> Default: no request within 0.5 s
    AwaitRequest --> Failed: sequence started early (overrun)
    Validate --> Build: request valid
    Validate --> Failed: stale, out of range, beam current, PV severity, or EVR link fault
    Default --> Build: mode 0
    Build --> Load
    Build --> Failed: invalid mode or no end of sequence
    Load --> AwaitStart: EVG idle → write E1:SEQ1, enable, singleShot
    AwaitStart --> AwaitPrecompletion: sequence active
    AwaitStart --> Default: timeout (5 s)
    Failed --> AwaitPrecompletion: update fault code and failed count
```

| Step | What happens |
|---|---|
| Start | Force `INJ:injCycleEnable` to 0 (single-shot mode) and wait for all PV connections. |
| Await potentate | Wait for `TimPotentate` to be set. |
| Await precompletion | Wait for the event generator to reach the precompletion point of the current sequence (sequencer *busy* bit clears). Requests arriving now are ignored. After 5 s, assume the generator is stuck and send a default sequence. |
| Await request | Wait up to **0.5 s** for a new `TimInjReq`. No request → send a default (mode 0) sequence. If a sequence starts before one is loaded, count a start overrun. |
| Validate | Reject a stale sequence number, out-of-range buckets or bunch count, bad beam current (SR Injection mode only), alarmed event generator status PVs, or invalid EVR links. |
| Build | Look up the events for the mode, compute each event's time stamp (from target buckets, bunch count, and field-sync delays), drop gun events if inhibited, add the end-of-sequence event, sort by time stamp, and convert to `delay, event, category` triples. |
| Load | When the event generator is idle: write the alignment settings, booster extraction delays, and `E1:SEQ1`; enable SEQ1; trigger `INJ:singleShot`; update the success count and monitor records. |
| Await start | Wait for the sequence to become active. After 5 s, send a default sequence. |

All states watch for lost PV connections, `TimPotentate` being cleared, and `INJ:injCycleEnable` being set by someone else, and react by disabling repetitive cycles and returning to the appropriate wait state.

---

## Fault Codes

`InjSeqFaultCode` values:

| Value | State | Meaning |
|--:|---|---|
| 0 | *(blank)* | Success |
| 1 | Missing Connection | Not all PVs are connected |
| 2 | Start Overrun | A sequence started before the next one could be loaded |
| 3 | Stale Sequence | Sequence number unchanged from the last request |
| 4 | Invalid Mode | Unknown injection mode |
| 5 | Invalid Bucket | SR or AR bucket out of range |
| 6 | Invalid Bunches | Bunch count out of range |
| 7 | Invalid Beam Current | `SR:DCCT:AVG` INVALID in SR Injection mode |
| 8 | Excessive Beam Current | `SR:DCCT:AVG` above 510 mA in SR Injection mode |
| 9 | PV Severity | Event generator status PVs in alarm |
| 10 | Bad EVR/Link | `TimAllEVRvalid` not OK |
| 11 | No EOS | Generated sequence has no end-of-sequence event |

---

## AR/SR Swap-out

There is no SNL program for the second event generator, since the swap-out trigger events always occur at the same point relative to the AR/SR coincidence. The event generator records involved are:

- `$(P)$(R)E2:SEQ0`
- `$(P)$(R)E2:SEQ0:enable`
- `$(P)$(R)swapoutTrigger`

Selection of the bunch trains to swap is handled by the kicker driver IOC, since the kicker drivers have the required delay resolution and the event system does not. The EPICS client controlling swap-out updates the kicker driver timing, then triggers a swap-out with `swapoutTrigger`.

---

## IOC Instances

| Instance (`iocBoot/…`) | `$(T)` | Default EVG IP |
|---|---|---|
| `iocDualTiming` | *(empty — production)* | `131.243.93.169` |
| `iocDualTimingTest` | `test` | `192.168.1.167` |
| `iocDualTimingARInjection` | `arTest` | `192.168.1.146` |

Override the address with the `IP` environment variable and the prefix with `DUAL_TIMING_IOC_TEST`. Each instance runs:

```
iocshLoad("$(IOCSH_LOCAL_TOP)/timing.iocsh", "PORT=$(PORT),P=$(P),R=$(R),IP=$(IP)")
seq timingSequence "P=$(P),R=$(R),T=$(T)"
```

`timing.iocsh` configures the event generator port and loads `eventGenerator.db`, `timing.db`, `alsGblPVs.db`, and `alsGblPVsInjReqAssembly.db`.

---

## Operator Screens and Scripts

Phoebus screens in `op/bob` (launch with `runPhoebus.sh`):

| Screen | Contents |
|---|---|
| `TIM_injectionSequencer.bob` | Injection requests and sequencer status |
| `TIM_debugControl.bob` | Sequencer debug controls |

Scripts in `scripts`:

| Script | Purpose |
|---|---|
| `fakeTimingSystem.py` | Act as the facility timing system to exercise the dual event generator. Options include `-c` cycle count, `-a` AR injection, `-w` wait for each injection, `-m` monitor sequences. |
| `injectUntilBRBucket.py` | Keep injecting until the booster reaches a given bucket (`-b`). |
| `chkAlign.py` | Show event streams from the old and new timing systems side by side. |
| `console.py` | Connect to the FPGA console (`-a` address, default `131.243.196.245`). |
