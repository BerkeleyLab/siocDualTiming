#!/bin/bash

set -eu

prefix="EVG:"
bob="TIM_injectionSequencer.bob"

SCRIPTPATH="$( cd "$( dirname "${BASH_SOURCE[0]}"  )" && pwd  )"

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

for i in "$@"
do
    case "$i" in
    *.bob)  bob="$i" ;;
    *)      prefix="$i" ;;
    esac
done

P=`echo "$prefix" | sed -ne '/\(.\).*/s//\1/p'`
R=`echo "$prefix" | sed -ne '/.\(.*\)/s//\1/p'`
EVG=`getPath EVG`

ln -sf $EVG/op/bob/autoconvert/*.bob autoconvert/

phoebus -resource file:${SCRIPTPATH}/autoconvert/${bob}?"P=${P}&R=${R}&T=${P}${R}"
