#!/bin/bash
export OLM_HOME="/home/fmeyer/"
export OLM_ROOT="/home/fmeyer/observatoire_moutherot"
export OLM_LOGDIR="$OLM_ROOT/log"
export OLM_LOG="$OLM_LOGDIR/olm.log"
export OLM_DAEMONLOG="$OLM_LOGDIR/relayd.log"
export OLM_SERVERLOG="$OLM_LOGDIR/relayserver.log"
export OLM_R8_STATE="/tmp/olm_relay8"
export OLM_R16_STATE="/tmp/olm_relay16"
export OLM_R8_SEM="/tmp/olm_r8_sem"
export OLM_R16_SEM="/tmp/olm_r16_sem"
export OLM_SHUTDOWN_SEM="/tmp/shutdown_sem"
export OLM_EQ8TSYNC="/tmp/olm_eq8tsynced"
export OLM_SETTIMEOUT=5
export OLM_R16TIMEOUT=60

export OLM_INDIHOST="192.168.0.26"
export OLM_RELAY8IP="192.168.0.23"
export OLM_RELAY16IP="192.168.0.28"
export OLM_RELAY8PORT="2380"

export OLM_BASER8="http://fmeyer:4so4xRg9@${OLM_RELAY8IP}:${OLM_RELAY8PORT}/relays.cgi"
export OLM_BASER16="http://${OLM_RELAY16IP}/30"

export OLM_INDIROOT=$OLM_ROOT/indi
export OLM_INDIRUN=$OLM_INDIROOT/run
export OLM_INDILOGDIR=$OLM_INDIROOT/log
export OLM_INDISERVERLOG=$OLM_INDILOGDIR/server.log
export OLM_INDIFIFO=$OLM_INDIROOT/indififo
export OLM_INDIWRAPLOG=$OLM_INDIROOT/wraplog
export OLM_INDIWRAPPIDFILE=$OLM_INDIRUN/wrap.pid
export OLM_INDISERVPIDFILE=$OLM_INDIRUN/indiserver.pid
export OLM_INDILOCALDRIVERS=$OLM_INDIROOT/indilocaldrivers
export OLM_PYRSCFILE=$OLM_INDIROOT/gpio_filter_assignments.py

export olm_fw_fifoname=$(grep olm_fw_fifoname $PYRSCFILE |awk -F= '{print $2}'|tr -d '"')
export olm_fw_statefile=$(grep olm_fw_statefile $PYRSCFILE |awk -F= '{print $2}'|tr -d '"')

daemonlog(){
    date +"%Y%m%d_%H%M%S_%Z : $1" >>$OLM_DAEMONLOG 2>&1
}

olm_log() {
    echo $(date +"%H:%M:%S ") $* >>$OLM_LOG
    }

setr8_usage(){
cat <<ENDUSAGE
    usage ${FUNCNAME[0]} channel 
    channel   description :
    LIGHT     lumiere
    PILIER    pilier
    CAM       camera
    PCN       prises Nord
    PCS       prises Sud (dont toit)
    R16       relais 16 ports
ENDUSAGE
}

setr16_usage(){
cat <<ENDUSAGE
    usage ${FUNCNAME[0]} channel 0|1
    channel   description
    USB       hub usb
    EQ8       eq8 mount
    INDI      indi host 
    DEW       dew heater
    ATK       atik cam
    FWST      filter wheel stepper
    14ST      C14 focuser stepper
    TSST      TS focuser stepper
    RFOP      ROOF OPEN
    RFST      ROOF STOP
    RFCL      ROOF CLOSE
ENDUSAGE
}

olm_setr8(){
    switch="$1"
    if test -z "$switch"; then
        setr8-usage
        return
    fi
    shift
    setstate="$1"
    if test -z "$setstate"; then
        setr8-usage
        return
    fi

    case $switch in 
        LIGHT)
            let addr=1
            ;;
        PILIER)
            let addr=2
            ;;
        CAM)
            let addr=3
            ;;
        PCN)
            let addr=4
            ;;
        PCS)
            let addr=5
            ;;
        R16)
            let addr=6
            ;;
        *)
            return ;;
    esac
    read -a relay <<<$(grep Status $OLM_R8_STATE)
    if ! test "${relay[$addr]}" = "$setstate"; then
        olm_log "     ${FUNCNAME[0]}: switching $switch to $setstate, ${OLM_BASER8}?relay=$addr"
        curl --connect-timeout 5 -o /dev/null "${OLM_BASER8}?relay="$addr  >/dev/null 2>/dev/null
    else
        olm_log "     ${FUNCNAME[0]}: $switch already to $setstate, not switching."
    fi
}

olm_setr16(){

    switch="$1"
    ad="$2"
    if test -z "$switch"; then
        setr16-usage
        return
    fi

    if test -z "$ad"; then
        setr16-usage
        return
    fi

    if ! test "$ad" = "1"; then
        if ! test "$ad" = "0"; then
            setr16-usage
            return
        fi
    fi

    case $switch in 
        USB)
            let addr=22+$ad
            ;;
        EQ8)
            let addr=24+$ad
            ;;
        OID)
            let addr=18+$ad
            ;;
        DEW)
            let addr=16+$ad
            ;;
        ATK)
            let addr=20+$ad
            ;;
        FWST)
            let addr=$ad
            addr="0$addr"
            ;;
        C14ST)
            let addr=2+$ad
            addr="0$addr"
            ;;
        TSST)
            let addr=4+$ad
            addr="0$addr"
            ;;
        RFOP)
            let addr=26+$ad
            ;;
        RFST)
            let addr=28+$ad
            ;;
        RFCL)
            let addr=30+$ad
            ;;
    esac
    olm_log "     ${FUNCNAME[0]}: setting $switch to $ad, ${OLM_BASER16}/$addr"

    curl --connect-timeout  $OLM_SETTIMEOUT -o /dev/null "${OLM_BASER16}/"$addr  >/dev/null 2>/dev/null
}

olm_wait_r16(){
    #
    # this waits forever. Might need FIXME
    #
    olm_log "    ${FUNCNAME[0]} : waiting for r16 to come up"
    while ! test "$result" = "0"; do
        curl --connect-timeout $OLM_R16TIMEOUT --max-time $OLM_R16TIMEOUT -o /dev/null "${OLM_BASER16}" \
                >/dev/null 2>/dev/null
        result="$?"
    done
    olm_log "    ${FUNCNAME[0]} : r16 is up"
}

olm_cold_init(){
    #
    # do not initialize over a previous shutdown, unless arg "force" is given
    #
    if ! test -f "$OLM_SHUTDOWN_SEM" || test "$1" = "force"; then
        olm_log "  ${FUNCNAME[0]} : starting init sequence"
        olm_init_r8_full
        # allow 60 s for relay16 to come up :
        if test "$?" ="0"; then
            olm_init_r16_full
            olm_log "  ${FUNCNAME[0]} : init over"
        else
            olm_log "${FUNCNAME[0]} : error connecting r16, not initializing it"
            olm_log "  ${FUNCNAME[0]} : init failed"
        fi
    else
        olm_log "  ${FUNCNAME[0]} : 'force' arg not passed: not overriding previous shutdown... "
    fi
    }

olm_init_r8_full(){
    olm_log "    ${FUNCNAME[0]} : starting init r8"
    delay=1
    olm_setr8 R16 1
    sleep $delay
    olm_setr8 PILIER 1
    sleep $delay
    olm_setr8 CAM 1
    sleep $delay
    olm_setr8 PCN 1
    sleep $delay
    olm_setr8 PCS 1
    sleep $delay
    olm_log "  ${FUNCNAME[0]} : exiting"
    }

olm_init_r16_full(){
    olm_log "    ${FUNCNAME[0]} : starting init r16"
    olm_wait_r16
    delay=2
    olm_setr16 USB 1 wait
    sleep $delay
    olm_setr16 EQ8 1
    sleep $delay
    olm_setr16 DEW 1
    sleep $delay
    olm_setr16 ATK 1
    sleep $delay
    olm_setr16 FWST 1
    sleep $delay
    olm_setr16 C14ST 1
    sleep $delay
    olm_setr16 TSST 1
    sleep $delay
    olm_setr16 OID 1
    olm_log "  ${FUNCNAME[0]} : exiting"
}

olm_off_r16_full(){
    olm_log "    ${FUNCNAME[0]} : shutting down r16"
    delay=1
    olm_setr16 OID 0
    sleep $delay
    olm_setr16 USB 0
    sleep $delay
    olm_setr16 EQ8 0
    sleep $delay
    olm_setr16 DEW 0
    sleep $delay
    olm_setr16 ATK 0
    sleep $delay
    olm_setr16 FWST 0
    sleep $delay
    olm_setr16 C14ST 0
    sleep $delay
    olm_setr16 TSST 0
    olm_log "    ${FUNCNAME[0]} : r16 shutdown complete"
    rm -f $OLM_R16_SEM
}

olm_off_r8_full(){ 
    olm_log "    ${FUNCNAME[0]} : starting r16 shutdown"
    delay=1
    olm_setr8 LIGHT 0
    sleep $delay
    olm_setr8 PILIER 0
    sleep $delay
    olm_setr8 CAM 0
    sleep $delay
    olm_setr8 PRN 0
    sleep $delay
    olm_setr8 PRS 0
    sleep $delay
    olm_setr8 R16 0
    rm -f $OLM_R8_SEM

    olm_log "    ${FUNCNAME[0]} : r8 shutdown complete"
}

olm_shutdown_indihost(){
    olm_log "    ${FUNCNAME[0]} : shutting down indi host $OLM_INDIHOST"
    olm_indicmd "sudo shutdown"
}

olm_fullshutdown(){ 
    olm_log "    ${FUNCNAME[0]} : starting full shutdown"
    olm_shutdown_indihost
    sleep 5
    olm_off_r16_full 
    olm_off_r8_full
    olm_log "    ${FUNCNAME[0]} : full shutdown completed"
    touch $OLM_SHUTDWN_SEM
}

olm_indicmd(){
    olm_log ssh -i $HOME/.ssh/obsm $OLM_INDIHOST $*
    ssh -i $HOME/.ssh/obsm fmeyer@$OLM_INDIHOST $*
}
 
olm_fw_get_filter(){

    ping -c 1 -W 1 "$OLM_INDIHOST" >/dev/null 2>&1
    if test "$?" = "0"; then
        olm_indicmd fw_get
    else
        echo "notup"
    fi
    }

olm_fw_set_filter(){
    ping -c 1 -W 1 "$OLM_INDIHOST" >/dev/null 2>&1
    if test "$?" = "0"; then
        if test -n "$1"; then
            olm_indicmd fw_set "$1"
        fi
        olm_indicmd fw_get
    else
        echo "notup"
    fi
}

olm_get_indi_status(){
#
# getting indi status running on indi host
#
    ping -c 1 -W 1 $OLM_INDIHOST >/dev/null 2>&1
    if test "$?" = "0"; then
        echo OK
        olm_indicmd olm_in_status_all 
    else
        echo notup
    fi
}

olm_get_relay_state(){
    wd=/tmp

    arg="$1"
    if test "$1" = ""; then
        # echo will do 16 by default
        arg="16"
    fi

    if test "$arg" = "16"; then
        failed=""
        ping -c 1 -W 1 $OLM_RELAY16IP >/dev/null 2>&1
        if test "$?" = "0"; then
            echo OK
            for i in $(seq 0 3); do
                rm -rf $OLM_R16_STATE-$i
                # wget --no-cache ${OLM_BASER16}/43 --timeout=1 --tries=2 -O $OLM_R16_STATE-$i >/dev/null 2>&1
                curl --connect-timeout "$OLM_SETTIMEOUT"  ${OLM_BASER16}/43 -o $OLM_R16_STATE-$i >/dev/null 2>&1
                # curl  ${OLM_BASER16}/43 --output $outfile-$i >/dev/null 2>&1
                if ! test "$?" = "0"; then
                    failed="1"
                    break
                fi
            done
            if test "$failed" = ""; then
                cat $OLM_R16_STATE-[0-3] \
                    |sed 's/<p>R/<p> R/g;s/<p> R/\n<p> R/g;s@&nbsp@@g' \
                    |grep 'Relay...:' \
                    |sed 's@<center.*@@;s@<small>.*</small>@@;s@> ON/@>ON/@;s@>O@ >O@g;s@</font>@@;s@028@0.28@;s@href=@@;s@"@@g'\
                    |awk '{print $2 " " $5 " " $7}'
                rm -f $OLM_R16_STATE-[0-3]
            else
                echo notup
            fi
        else
            echo notup
        fi
    fi

    if test "$arg" = "8"; then
        ping -c 1 -W 1 ${OLM_RELAY8IP} >/dev/null 2>&1
        if test "$?" = "0"; then
            echo OK
            # /usr/bin/wget -O $OLM_R8_STATE ${OLM_BASER8} --timeout=2 --tries=2 >/dev/null 2>/dev/null 
            curl --connect-timeout "$OLM_SETTIMEOUT"  ${OLM_BASER8} -o $OLM_R8_STATE >/dev/null 2>&1
            if test "$?" = "0"; then
                cat "$OLM_R8_STATE" |grep ': '|sed -E 's/ *[^ ]+ *//'
            else
                echo notup
            fi
        else
            echo notup
        fi
    fi
    }

olm_in_log(){
    date +"%Y%m%d_%H%M%S_%Z : $1" >>$OLM_INDIWRAPLOG 2>&1
    }

olm_in_sync_eq8_time(){
    # init time 
    #
    if ! test -f /tmp/synced; then
        /usr/bin/indi_setprop "EQMod Mount.CONNECTION.CONNECT=On"
        setutc=$(date +"EQMod Mount.TIME_UTC.UTC=%Y-%m-%dT%H:%M:%S;OFFSET=0.00")
        if /usr/bin/indi_setprop "$setutc"; then
            olm_in_log "set EQ8 UTC : $setutc"
            rm -f /tmp/sync-failed
            touch /tmp/synced
        else
            rm -f /tmp/synced
            touch /tmp/sync-failed
        fi
    fi
}

olm_in_dname(){
    case $1 in
        indiserver|indi_atik_ccd|indi_eqmod_telescope|indi_qhy_ccd|indi_atik_wheel|indi_canon_ccd|fw.py)
            driver=$1;;
        atik) driver=indi_atik_ccd;;
        eq8) driver=indi_eqmod_telescope;;
        qhy) driver=indi_qhy_ccd;;
        fw) driver=fw.py;;
        eos) driver=indi_canon_ccd;;
        asi) driver=indi_asi_ccd;;
        *) driver="";;
    esac
    export driver
    }

olm_in_wrap(){
    #
    # if arg 1 is "init" then localdrivers listed in OLM_INDILOCALDRIVERS
    # will be initialized
    #
    if [[ "$1" == "init" ]]; then
        olm_in_start_all
    fi
    }

olm_in_killserv(){
    echo killing server $(cat $OLM_INDISERVPIDFILE) |tee -a $OLM_INDISERVERLOG
    kill $(cat "$OLM_INDISERVPIDFILE")
    rm $OLM_INDISERVPIDFILE
    }

olm_in_killdrivers(){
    while read driver; do
        [[ $driver =~ ^# ]] ||
        olm_in_stop $driver
    done <$OLM_INDILOCALDRIVERS
    }

olm_in_killall(){
    echo killing wrapper $(cat $OLM_INDIWRAPPIDFILE) |tee -a $OLM_INDISERVERLOG
    kill -INT $(cat "$OLM_INDIWRAPPIDFILE")
    rm $OLM_INDIWRAPPIDFILE
    rm $OLM_INDISERVPIDFILE
    olm_in_killserv
    olm_in_killdrivers
    }

olm_in_start(){
    olm_in_log ${FUNCNAME[0]}
    olm_in_dname $1
    if [[ $driver == "fw.py" ]]; then
        nohup $OLM_INDIROOT/$driver daemon >> $OLM_INDISERVERLOG 2>&1 &
    else
        if [[ "$driver" == "indiserver" ]]; then
            nohup /usr/bin/indiserver -f $OLM_INDIFIFO >> $OLM_INDISERVERLOG 2>&1 &
        else
            pid=$(pidof $driver)
            if [[ $? != 0 ]]; then
                echo start $driver |tee -a $OLM_INDIFIFO
                driverpid=$(pidof $driver)
                echo $driver running : $driverpid |tee -a $OLM_INDISERVERLOG
                echo -n "$driverpid " >> $OLM_INDIRUN/$driver.pid
            else
                echo existing driver $driver pid $pid
            fi
        fi
    fi
    olm_in_log /${FUNCNAME[0]}
    }

olm_in_pidof(){
    olm_in_dname $1
    if [[ "$driver" == "" ]]; then
        echo
    else
        pid=$(pidof -x $driver -o %PPID)
        if [ "$?" = "0" ]; then
            echo  $pid >$OLM_INDIRUN/$driver.pid
            if [[ "$2" == "" ]]; then
                echo $1 $pid
            fi
        else
            echo $1 not_running
            if test -f $OLM_INDIRUN/$driver.pid; then
                rm -f $OLM_INDIRUN/$driver.pid
            fi
            return 255
        fi
    fi
    }

olm_in_status(){
    if test -n "$1"; then
        olm_in_dname $1
        olm_in_pidof $driver
    else
        olm_in_status_all
    fi
    }

olm_in_status_all(){
    echo -n "server "
    olm_in_status indiserver
    while read driver; do
        [[ $driver =~ ^# ]] ||
        (echo -n "$driver " && olm_in_status $driver)
    done <$OLM_INDILOCALDRIVERS
    }

olm_in_start_all(){
    olm_in_log ${FUNCNAME[0]}
    olm_in_log Starting drivers
    while read driver; do
        [[ $driver =~ ^# ]] ||
        olm_in_start $driver
    done <$OLM_INDILOCALDRIVERS
    olm_in_log /$FUNCNAME{0}
    }

olm_in_stop_all(){
    olm_in_log ${FUNCNAME[0]}
    olm_in_log Stopping all drivers
    while read driver; do
        [[ $driver =~ ^# ]] ||
        olm_in_stop $driver
    done <$OLM_INDILOCALDRIVERS
    olm_in_log Stopping indiserver
    olm_in_killserv 
    olm_in_log Done
    olm_in_log /${FUNCNAME[0]}
    }

olm_in_stop(){
    olm_in_log ${FUNCNAME[0]}
    olm_in_dname $1
    if [[ $driver == "fw.py" ]]; then
        #
        # non-INDI processes here :
        kill -SIGINT $(pidof -x $driver -o %PPID)
    else
        #
        # INDI drivers here, including server :
        if [[ $driver == "indiserver" ]]; then
            olm_in_stop_all
        else
            olm_in_log stopping $driver
            echo stop $driver |tee $OLM_INDIFIFO
        fi
    fi
    olm_in_log /${FUNCNAME[0]}
    }

olm_in_cycle(){
    olm_in_log ${FUNCNAME[0]}
    olm_in_log START CYCLE 
    olm_in_dname $1
    if [[ $1 == "indiserver" ]]; then
        olm_in_log Cycling indiserver
        olm_in_stop_all
        olm_in_log Starting indiserver
        olm_in_start indiserver
        sleep 1
        olm_in_start_all
    else
        olm_in_log olm_in_stop $driver
        olm_in_stop $driver
        olm_in_log sleeping 1s
        sleep 1
        olm_in_log olm_in_start $driver
        olm_in_start $driver
    fi
    olm_in_log END CYCLE 
    olm_in_log /${FUNCNAME[0]}
    olm_in_log ==========================
    }

olm_fw_set(){
    if test -n "$1"; then
        if test -n "$(pidof -x fw.py)"; then
            echo $1 >$olm_fw_fifoname
        else
            echo "# fw.py is not running"
        fi
    fi
    sleep 2
    olm_fw_get
}

olm_fw_get(){
    cat $olm_fw_statefile
}

olm_fw_start(){
    nohup $OLM_INDIROOT/fw.py daemon >/dev/null 2>&1 &
}

olm_fw_stop(){
    echo STOP >$olm_fw_fifoname
}

olm_fw_pwrstepper(){
    case "$1" in
        "ON")
            wget -O /dev/null http://192.168.0.28/30/01
            ;;
        "OFF")
            wget -O /dev/null http://192.168.0.28/30/00
            ;;
    esac
}

if test -n "$1"; then
    $*
fi
