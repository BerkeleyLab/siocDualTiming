# ALS-U Dual Timing Soft IOC

Soft IOC that builds and sends injection sequences to the ALS-U dual event generator. A state notation language program turns injection requests (`TimInjReq`) into event sequences and triggers them on the injector event generator. The IOC also loads the full event generator database from the [DualEventGeneratorSupport](https://git.als.lbl.gov/accelerator-controls/epics/iocs/DualEventGeneratorSupport) module, so one IOC both runs the sequencer and talks to the FPGA.

## Repository layout

| Path | Contents |
|---|---|
| `timingApp/src` | Sequencer program (`timingSequence.st`), request assembly, and the per-mode event tables generated from `TuningModeTriggers.csv` |
| `timingApp/Db` | Timing record database |
| `iocBoot/iocDualTiming` | Production IOC |
| `iocBoot/iocDualTimingTest` | Test IOC (`test` record prefix) |
| `iocBoot/iocDualTimingARInjection` | AR injection test IOC (`arTest` record prefix) |
| `op/bob` | Phoebus screens |
| `scripts` | `fakeTimingSystem.py`, `injectUntilBRBucket.py`, and other utilities |
| `documentation` | User documentation |

## Building

Requires EPICS base with the asyn, seq, std, calc, autosave, recsync, retools, caPutLog, iocStats, pvxs, and siteApps modules, plus **DualEventGeneratorSupport**. Set `EPICS_BASE` and `EVENTGENERATORSUP` in `configure/RELEASE.local`, then:

```sh
make
```

## Running

```sh
cd iocBoot/iocDualTiming
./st.cmd
```

Set the event generator address with the `IP` environment variable and the record prefix with `DUAL_TIMING_IOC_TEST` (empty for production). `./run` and `./rund` start the IOC in a `screen` session (foreground or detached), and `./attach` reconnects to it.

## Documentation

📖 **[documentation/README.md](documentation/README.md)** — injection requests, records, state machine, fault codes, and IOC instances.

## Related projects

| Project | Contents |
|---|---|
| [DualEventGeneratorSupport](https://git.als.lbl.gov/accelerator-controls/epics/iocs/DualEventGeneratorSupport) | EPICS support module for the event generator |
| [dual-evg](https://gitlab.lbl.gov/alsu-instrumentation/dual-evg) | Event generator hardware, gateware, and µBlaze software |
