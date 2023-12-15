#!/bin/sh

T="test"
E="TIM_injectionSequencer.edl"

SCRIPTPATH=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)

getPath() {
    for d in $SCRIPTPATH $SCRIPTPATH/.. $SCRIPTPATH/../..
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

for i
do
    case "$i" in
    *.edl)       E="$i"  ;;
    *)           T="$i"  ;;
    esac
done

case "$T" in
    "") MARG="T=\"$T\",P=EVG,R=:" ;;
    *)  MARG="T=$T,P=$T,R=EVG:"   ;;
esac

EVG=`getPath EVG`
export EDMDATAFILES=".:$EVG/opi"

edm -eolc -x -m "${MARG}" "$E" &
