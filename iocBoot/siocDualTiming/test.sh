#!/bin/sh

# Start soft IOC in test mode
export EVG_ADDRESS="${EVG_ADDRESS=192.168.1.129}"
export FPGA_SIMM_DISABLE="#"
export FPGA_TRACK_DISABLE="#"
export SEQ_DEBUG="0"
for i in "$@"
do
    case "$i" in
        [0-9]*)  EVG_ADDRESS="$1" ;;
        -s) FPGA_SIMM_DISABLE="" ;;
        -t) FPGA_TRACK_DISABLE="" ;;
        -d) SEQ_DEBUG="1" ;;
        -a) export AUTOSAVE_PATH="\$(TOP)/autosave" ;;
        -*) echo "Usage: $0 [-a] [-d] [-h] [-s] [-t] [EVG_ADDR]" >&2
            echo "       -a -- Use local autosave/restore directory" >&2
            echo "       -d -- Enable injection sequence program diagnostic messages" >&2
            echo "       -h -- Show this help messdage, then exit" >&2
            echo "       -s -- Place EVG records into simulation mode" >&2
            echo "       -t -- Track old timing system" >&2
            exit 1 ;;
    esac
done
export P="testEVG"
export R=":"
export T="dual"
./st.cmd
