import argparse
import epics
from FakeTimingSystem import TimingSystem

def _pv(name):
    """Connect to a PV and return it, raising an error on failure."""
    pv_obj = epics.PV(name, connection_timeout=1.0)
    pv_obj.get()
    if not pv_obj.connect():
        # Raise an exception instead of sys.exit() so calling scripts can handle the failure
        raise RuntimeError(f'Unable to connect to "{name}"')
    return pv_obj

def main():
    """Parses command-line arguments and initiates the TimingSystem the test """
    parser = argparse.ArgumentParser(
        description='Keep injecting unitl BR bucket is the desired one.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-e', '--evg', default='testEVG:', help='Event generator record name prefix')
    parser.add_argument('-m', '--monitor', action='store_true', help='Monitor and display event sequences')
    parser.add_argument('-t', '--test', default='test', help='Timing system test prefix')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show outgoing requests')
    parser.add_argument('-b', '--br-bucket', type=int, help='BR bucket to wait for', required=True)

    args = parser.parse_args()
    br_bucket_pv = _pv('testEVG:INJ:tgtBRBucket')
    event_10_PV = _pv('BL01:UT1:EVR:event10trig')
    event_11_PV = _pv('BL01:UT1:EVR:event11trig')

    # Set EVR to trigger on the event
    if True:
        event_10_PV.put(0)
        event_11_PV.put(1)

    try:
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
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
