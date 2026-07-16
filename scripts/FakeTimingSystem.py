from __future__ import print_function
import argparse
import epics
import sys
import time

class TimingSystem:
    def __init__(self, evg_prefix='testEVG:', test_prefix='test', monitor=False, verbose=False, ar_injection=False, wait_for_injection=False):
        self.evg_prefix = evg_prefix
        self.test_prefix = test_prefix
        self.monitor = monitor
        self.verbose = verbose
        self.ar_injection = ar_injection

        self.cycleDone = False
        self.wait_for_injection = wait_for_injection
        self.seqStatusWasBusy = None
        self.then = 0.0

    def _pv(self, name):
        """Connect to a PV and return it, raising an error on failure."""
        pv_obj = epics.PV(name, connection_timeout=1.0)
        pv_obj.get()
        if not pv_obj.connect():
            raise RuntimeError(f'Unable to connect to "{name}"')

        return pv_obj

    def _seqStatusCallback(self, pvname=None, value=None, **kws):
        if value is None:
            return
        seqStatIsBusy = (value & 0x10) != 0
        if self.seqStatusWasBusy is None:
            self.seqStatusWasBusy = seqStatIsBusy
        if not seqStatIsBusy and self.seqStatusWasBusy:
            self.cycleDone = True
        self.seqStatusWasBusy = seqStatIsBusy

    def _sequenceCallback(self, pvname=None, value=None, **kws):
        if value is None:
            return
        now = time.time()
        if self.then == 0:
            self.then = now
        print(f"+{now - self.then:.6f}")
        self.then = now
        i = 0
        while True:
            try:
                gap = value[i]
                evCode = value[i+1]
                cat = value[i+2]
                i += 3
                print(f"{gap}:{evCode}:{cat}")
                if evCode == 127:
                    break
            except IndexError:
                break

    def run(self, count=1):
        seqStatus = self._pv(self.evg_prefix + 'E1:seqStatus')
        seqStatus.add_callback(self._seqStatusCallback)

        if self.ar_injection:
            request_mode = 60
        else:
            request_mode = 40

        # Injection request mapping
        TARGET_BUCKET    = 0
        # GUN_BUNCHES    = 1
        # INJ_MODE       = 2
        # GUN_INHIBIT    = 3
        # TARGET_AR_BUCKET = 4
        # FURURE_1       = 5
        SEQUENCE         = 6

        request = [1, 4, request_mode, 0, 1, 0, 1]
        request[SEQUENCE] = int(time.time())
        requestPV = self._pv(self.test_prefix + 'TimInjReq')
        bucketIndex = 0

        if self.monitor:
            # Show event generator updates
            sequence = self._pv(self.evg_prefix + 'E1:SEQ1')
            sequence.add_callback(self._sequenceCallback)

        # Send requests until count limit has been reached
        self.cycleDone = False
        while count > 0:
            while not self.cycleDone:
                time.sleep(0.05)
            self.cycleDone = False
            bucketIndex = bucketIndex % 328
            request[TARGET_BUCKET] = bucketIndex + 1
            request[SEQUENCE] += 1
            requestPV.put(request)
            if self.verbose:
                print(request)
            count -= 1

        if self.wait_for_injection:
            while not self.cycleDone:
                time.sleep(0.05)

        if self.monitor:
            time.sleep(1.0)


def main():
    """Parses command-line arguments and initiates the TimingSystem evg."""
    parser = argparse.ArgumentParser(
        description='Fake facility timing system to exercise dual event generator.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-c', '--count', type=int, default=1, help='Number of cycles to request')
    parser.add_argument('-e', '--evg', default='testEVG:', help='Event generator record name prefix')
    parser.add_argument('-m', '--monitor', action='store_true', help='Monitor and display event sequences')
    parser.add_argument('-t', '--test', default='test', help='Timing system test prefix')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show outgoing requests')
    parser.add_argument('-w', '--wait-for-injection', action='store_true', help='Wait for EVG to finish last injection')
    parser.add_argument('-a', '--ar-injection', action='store_true', help='Inject into AR')

    args = parser.parse_args()

    try:
        evg = TimingSystem(
            evg_prefix=args.evg,
            test_prefix=args.test,
            monitor=args.monitor,
            verbose=args.verbose,
            ar_injection=args.ar_injection,
            wait_for_injection=args.wait_for_injection
        )
        evg.run(count=args.count)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
