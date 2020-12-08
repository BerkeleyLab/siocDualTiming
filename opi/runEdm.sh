#!/bin/sh

T="test"
E="TIM_injectionSequencer.edl"

getPath() {
    for d in . ..
    do
        if [ -r "$d/Makefile" -a -r "$d/configure/RELEASE" ]
        then
            (
            cd "$d"
            SVIFS="$IFS"
            IFS="=$IFS"
            set -- `make -pn | grep "^ *$1 *="`
            IFS="$SVIFS"
            echo "$2"
            )
            break
        fi
    done 
}

ARGS="$@"

EVG=`getPath EVG`
export EDMDATAFILES=".:$EVG/opi"

for i in $ARGS
do
    case "$i" in
    *.edl)       E="$i"  ;;
    *)           T="$i"  R=":" ;;
    esac
done

case "$T" in
    "") TARG="T=\"$T\"" ;;
    *)  TARG="T=$T"     ;;
esac

edm -eolc -x -m "${TARG}" "$E" &
