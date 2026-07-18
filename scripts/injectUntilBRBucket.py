import argparse
import sys
import epics
from FakeTimingSystem import TimingSystem


def get_pv(name: str, timeout: float = 1.0) -> epics.PV:
    """Connect to a PV and return it, raising an error on failure."""
    pv_obj = epics.PV(name, connection_timeout=timeout)
    if not pv_obj.wait_for_connection(timeout=timeout):
        raise RuntimeError(f'Unable to connect to "{name}"')
    return pv_obj


def main() -> None:
    """Parses command-line arguments and initiates the TimingSystem test."""
    parser = argparse.ArgumentParser(
        description='Keep injecting until BR bucket is the desired one.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-e', '--evg', default='testEVG:', help='Event generator record name prefix')
    parser.add_argument('-p', '--evr-prefix', default='BL01:UT1:', help='EVR prefix')
    parser.add_argument('-m', '--monitor', action='store_true', help='Monitor and display event sequences')
    parser.add_argument('-t', '--test', default='test', help='Timing system test prefix')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show outgoing requests')
    parser.add_argument('-b', '--br-bucket', type=int, help='BR bucket to wait for', required=True)

    args = parser.parse_args()

    try:
        br_bucket_pv = get_pv(f"{args.evg}INJ:tgtBRBucket")
        event_10_pv = get_pv(f"{args.evr_prefix}EVR:event10trig")
        event_11_pv = get_pv(f"{args.evr_prefix}EVR:event11trig")

        # Set EVR to trigger on the event
        event_10_pv.put(0)
        event_11_pv.put(1)

        evg = TimingSystem(
            evg_prefix=args.evg,
            test_prefix=args.test,
            monitor=args.monitor,
            verbose=args.verbose,
            ar_injection=True,
            wait_for_injection=True
        )

        br_bucket = int(br_bucket_pv.get())
        while br_bucket != args.br_bucket:
            evg.run(count=1)
            br_bucket = int(br_bucket_pv.get())
            print(f"BR bucket: {br_bucket}")

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
