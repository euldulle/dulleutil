#!/bin/bash
#
. /home/fmeyer/indi_env.sh

# first initialize time :
in_sync_eq8_time

mkdir -p $INDIBIN $INDIRSC $INDIRUN $INDILOGDIR
list=$(pidof -o $$ -x $(basename -- $0) )
if [[ $? == "0" ]]; then
    date +"%Y%m%d_%H:%M:%S : killing existing wrappers and servers " |tee -a $INDISERVERLOG
    kill -INT $list
    killall indiserver
    sleep 1
fi

stop=""
echo $0
echo $INDIWRAPPIDFILE
echo $$>$INDIWRAPPIDFILE

mkfifo $INDIFIFO >/dev/null 2>&1
date +"%Y%m%d_%H:%M:%S : starting indiserver, listening on $INDIFIFO " |tee -a $INDISERVERLOG
nohup /usr/bin/indiserver -f $INDIFIFO >> $INDISERVERLOG 2>&1 &
if [[ "$1" == "init" ]]; then
    in_wrap init
fi

while [[ $stop == "" ]]; do
    in_status indiserver quiet
    if [[ $? != "0" ]]; then
        date +"%Y%m%d_%H:%M:%S : indiserver died " |tee -a $INDISERVERLOG
        date +"%Y%m%d_%H:%M:%S : starting indiserver, listening on $INDIFIFO " |tee -a $INDISERVERLOG
        nohup /usr/bin/indiserver -f $INDIFIFO >> $INDISERVERLOG 2>&1 &
    fi
    in_status_all
    sleep 5
done
date +"%Y%m%d_%H:%M:%S : Bye." |tee -a $INDISERVERLOG
