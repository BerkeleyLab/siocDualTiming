#!/bin/sh

set -ex
export DUAL_TIMING_IOC_TEST="test"

exec ../../bin/linux-x86_64/timing st.cmd
