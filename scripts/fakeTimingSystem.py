import argparse
import sys
import time
from typing import Optional, Any

import epics


class TimingSystem:
    """Fake facility timing system to exercise dual event generator."""

    def __init__(
        self, 
        evg_prefix: str = 'testEVG:', 
        test_prefix: str = 'test', 
        monitor: bool = False, 
        verbose: bool = False, 
        ar_injection: bool = False, 
        wait_for_injection: bool = False
    ):
        self.evg_prefix = evg_prefix
        self.test_prefix = test_prefix
        self.monitor = monitor
        self.verbose = verbose
        self.ar_injection = ar_injection
        self.wait_for_injection = wait_for_injection

        self.cycle_done: bool = False
        self.seq_status_was_busy: Optional[bool] = None
        self.then: float = 0.0

    def _get_pv(self, name: str, timeout: float = 1.0) -> epics.PV:
        """Connect to a PV and return it, raising an error on failure."""
        pv_obj = epics.PV(name, connection_timeout=timeout)
        if not pv_obj.wait_for_connection(timeout=timeout):
            raise RuntimeError(f'Unable to connect to "{name}"')
        return pv_obj

    def _seq_status_callback(self, pvname: Optional[str] = None, value: Any = None, **kws: Any) -> None:
        if value is None:
            return

        seq_stat_is_busy = (value & 0x10) != 0
        if self.seq_status_was_busy is None:
            self.seq_status_was_busy = seq_stat_is_busy

        if not seq_stat_is_busy and self.seq_status_was_busy:
            self.cycle_done = True

        self.seq_status_was_busy = seq_stat_is_busy

    def _sequence_callback(self, pvname: Optional[str] = None, value: Any = None, **kws: Any) -> None:
        if value is None:
            return

        now = time.time()
        if self.then == 0.0:
            self.then = now
        print(f"+{now - self.then:.6f}")
        self.then = now

        for i in range(0, len(value), 3):
            chunk = value[i:i+3]
            if len(chunk) < 3:
                break

            gap, ev_code, cat = chunk
            print(f"{gap}:{ev_code}:{cat}")

            if ev_code == 127:
                break

    def run(self, count: int = 1) -> None:
        seq_status = self._get_pv(f"{self.evg_prefix}E1:seqStatus")
        seq_status.add_callback(self._seq_status_callback)

        request_mode = 60 if self.ar_injection else 40

        # Injection request mapping
        TARGET_BUCKET_IDX    = 0
        # GUN_BUNCHES_IDX    = 1
        # INJ_MODE_IDX       = 2
        # GUN_INHIBIT_IDX    = 3
        # TARGET_AR_BUCKET_IDX = 4
        # FURURE_1_IDX       = 5
        SEQUENCE_IDX         = 6

        request = [1, 4, request_mode, 0, 1, 0, 1]
        request[SEQUENCE_IDX] = int(time.time())
        request_pv = self._get_pv(f"{self.test_prefix}TimInjReq")
        bucket_index = 0

        if self.monitor:
            # Show event generator updates
            sequence = self._get_pv(f"{self.evg_prefix}E1:SEQ1")
            sequence.add_callback(self._sequence_callback)

        # Send requests until count limit has been reached
        self.cycle_done = False
        for _ in range(count):
            while not self.cycle_done:
                time.sleep(0.05)
            self.cycle_done = False

            bucket_index = bucket_index % 328
            request[TARGET_BUCKET_IDX] = bucket_index + 1
            request[SEQUENCE_IDX] += 1
            request_pv.put(request)

            if self.verbose:
                print(request)

        if self.wait_for_injection:
            while not self.cycle_done:
                time.sleep(0.05)

        if self.monitor:
            time.sleep(1.0)


def main() -> None:
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
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
