#!/bin/bash
export OLM_HOME="/home/fmeyer/"
export OLM_ROOT="/home/fmeyer/observatoire_moutherot"
export OLM_LOGDIR="$OLM_ROOT/log"
export OLM_LOG="$OLM_LOGDIR/olm.log"
#
export OLM_RDAEMON_NAME="relayd"
export OLM_RDAEMON_LOG="$OLM_LOGDIR/$OLM_RDAEMON_NAME.log"
export OLM_RSERVER_NAME="relay_server.py"
export OLM_RSERVER_LOG="$OLM_LOGDIR/${OLM_RSERVER_NAME}.log"
#
export OLM_IDAEMON_NAME="indid"
export OLM_IDAEMON_LOG="$OLM_LOGDIR/$OLM_IDAEMON_NAME.log"
#
export OLM_R8_STATE="/tmp/olm_relay8"
export OLM_R16_STATE="/tmp/olm_relay16"
export OLM_R8_SEM="/tmp/olm_r8_sem"
export OLM_R16_SEM="/tmp/olm_r16_sem"
export OLM_SHUTDOWN_SEM="/tmp/olm_shutdown_sem"
export OLM_EQ8TSYNC="/tmp/olm_eq8tsynced"
export OLM_EQ8TNOTSYNC="/tmp/olm_eq8tsyncfailed"
export OLM_SETTIMEOUT=5
export OLM_R16TIMEOUT=60

export OLM_NETWORK="192.168.1"
export OLM_IHOST="$OLM_NETWORK.26"
export OLM_R8IP="$OLM_NETWORK.23"
export OLM_R16IP="$OLM_NETWORK.28"
export OLM_R8PORT=""

export OLM_BASER8="http://fmeyer:4so4xRg9@${OLM_R8IP}${OLM_R8PORT}/relays.cgi"
export OLM_BASER16="http://${OLM_R16IP}/30"

export OLM_IROOT=$OLM_ROOT/indi
export OLM_IRUN=$OLM_IROOT/run
export OLM_ILOGDIR=$OLM_ROOT/log
export OLM_ISERVER_LOG=$OLM_ILOGDIR/server.log
export OLM_IFIFO=$OLM_IROOT/indififo
export OLM_ISERVPIDFILE=$OLM_IRUN/indiserver.pid
export OLM_ILOCALDRIVERS=$OLM_IROOT/indilocaldrivers
export OLM_PYRSCFILE=$OLM_IROOT/gpio_filter_assignments.py
export OLM_O2SHARE="$OLM_ROOT/o2oid"
export OLM_BATSTATUS=$OLM_O2SHARE/capstatus.txt

# this is for non indi wheels:
export olm_fw_fifoname=$(grep olm_fw_fifoname $OLM_PYRSCFILE |awk -F= '{print $2}'|tr -d '"')
export olm_fw_statefile=$(grep olm_fw_statefile $OLM_PYRSCFILE |awk -F= '{print $2}'|tr -d '"')

r8=("LIGHT Light"\
    "PIL Pilier"\
    "CAM Camera"\
    "PCN Prises-N"\
    "PCS Prises-S"\
    "R16 Relais-16"\
    "NC NA"\
    "NC NA" )

rserverlog(){
    # logging relayd
    date +"%Y%m%d_%H%M%S_%Z : $1" >>$OLM_RSERVER_LOG 2>&1
}

iserverlog(){
    # logging indid
    date +"%Y%m%d_%H%M%S_%Z : $1" >>$OLM_ISERVER_LOG 2>&1
    #printf "%(%Y%m%d_%H%M%S_%Z)T%s : $1\n" >>$OLM_ISERVER_LOG 2>&1
}

rdaemonlog(){
    # logging relayd
    date +"%Y%m%d_%H%M%S_%Z : $1" >>$OLM_RDAEMON_LOG 2>&1
}

idaemonlog(){
    # logging indid
    date +"%Y%m%d_%H%M%S_%Z : $1" >>$OLM_IDAEMON_LOG 2>&1
}

olm_log() {
    date +"%Y%m%d_%H%M%S_%Z : $*" >>$OLM_LOG 2>&1
    #echo $(date +"%Y%m%d_%H%M%S_%Z ") $* >>$OLM_LOG
    }

setr8_usage(){
cat <<ENDUSAGE
    usage ${FUNCNAME[0]} channel
    channel   description :
ENDUSAGE
    for i in 0 1 2 3 4 5 6 7; do
        echo $i ${r8[i]}
    done
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
	if ! test -f $OLM_R8_STATE; then
		curl --connect-timeout "$OLM_SETTIMEOUT"  ${OLM_BASER8} -o $OLM_R8_STATE >/dev/null 2>&1
	fi
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

olm_wait_r8(){
    #
    # this waits forever. Might need FIXME
    #
    result="1"
    let count=0

    olm_log "    ${FUNCNAME[0]} : waiting for r8 to come up"
    while ! test "$result" = "0"; do
        ping -c 1 -W 5 $OLM_R8IP >/dev/null 2>&1
        if test "$?" = "0"; then
			olm_log "    ${FUNCNAME[0]} : ping r8 OK"
			break
        fi

        olm_log "ping -c 1 -W 5 $OLM_R8IP"
		lognet=$(ip addr list dev eth0 |grep 'inet ')
        olm_log "$lognet"
        let count=$count+1
        if test "$count" -gt 10; then
            olm_log "    ${FUNCNAME[0]} : ping r8 failed >10 Times, cycling interface"
            sudo nmcli con up olm
            let count=0
        fi
    done

    result="1"
    let count=0
    while ! test "$result" = "0"; do
        curl -o /dev/null "${OLM_BASER8}" >/dev/null 2>/dev/null
		if test "$result" = "0"; then
            olm_log "    ${FUNCNAME[0]} : r8 up and running"
			break
		fi
        result="$?"
        let count=$count+1
        if test "$count" -gt 10; then
            olm_log "    ${FUNCNAME[0]} : curl r8 failed >10 times,cycling interface"
            sudo nmcli con up olm
            let count=0
        fi
    done
    olm_log "    ${FUNCNAME[0]} : r8 is up"
	return 0
}

olm_wait_r16(){
    #
    # this waits forever. Might need FIXME
    #
    result="1"
    let count=0

    olm_log "    ${FUNCNAME[0]} : waiting for r16 to come up"
    while ! test "$result" = "0"; do
        ping -c 1 -W 5 $OLM_R16IP >/dev/null 2>&1
		result="$?"
        if test "$result" = "0"; then
			olm_log "    ${FUNCNAME[0]} : ping r16 OK"
			break
        fi

        olm_log "ping -c 1 -W 5 $OLM_R16IP"
		olm_log "$(ip addr list dev eth0 |grep 'inet ')"
        let count=$count+1
        if test "$count" -gt 10; then
            olm_log "    ${FUNCNAME[0]} : ping r16 failed >10 Times, powercycling it"
            # first make sure PILIER is ON
			olm_setr8 PILIER 1
            olm_setr8 R16 0
            sleep 2
            olm_setr8 R16 1
            let count=0
        fi
    done

    result="1"
    let count=0
    while ! test "$result" = "0"; do
        curl --connect-timeout $OLM_R16TIMEOUT --max-time $OLM_R16TIMEOUT -o /dev/null "${OLM_BASER16}" \
                >/dev/null 2>/dev/null
		result="$?"
		if test "$result" = "0"; then
            olm_log "    ${FUNCNAME[0]} : r16 up and running"
			break
		fi
        let count=$count+1
        if test "$count" -gt 10; then
            olm_log "    ${FUNCNAME[0]} : curl r16 failed >10 times, powercycling it"
            olm_setr8 R16 0
            sleep 1
            olm_setr8 R16 1
            let count=0
        fi
    done
    olm_log "    ${FUNCNAME[0]} : r16 is up"
	return 0
}

olm_cold_init(){
    #
    # do not initialize over a previous shutdown, unless arg "force" is given
    #
    if ! test -f "$OLM_SHUTDOWN_SEM" || test "$1" = "force"; then
    #if ! test -f "$OLM_SHUTDOWN_SEM" ; then
        olm_log "  ${FUNCNAME[0]} : starting init sequence"
        olm_init_r8_full
        if test "$?" = 0; then
            olm_log "  ${FUNCNAME[0]} : R8 init OK"
        else
            olm_log "  ${FUNCNAME[0]} : R8 init failed"
        fi
        olm_init_r16_full
           if test "$?" = 0; then
            olm_log "  ${FUNCNAME[0]} : R16 init OK"
        else
            olm_log "  ${FUNCNAME[0]} : R16 init failed"
        fi
        olm_init_r16_full
     olm_log "  ${FUNCNAME[0]} : init over"
    else
        olm_log "  ${FUNCNAME[0]} : 'force' arg not passed: not overriding previous shutdown... "
    fi
    }

olm_init_r8_full(){
	olm_wait_r8
    olm_log "    ${FUNCNAME[0]} : starting init r8"
    olm_setr8 PILIER 1
    olm_setr8 R16 1
    olm_setr8 CAM 1
    olm_setr8 PCN 1
    olm_setr8 PCS 1
    olm_log "  ${FUNCNAME[0]} : exiting"
	return 0
    }

olm_init_r16_full(){
    olm_log "    ${FUNCNAME[0]} : starting init r16"
    olm_wait_r16
	if test "$?" = "0"; then
		olm_log "    ${FUNCNAME[0]} : relay 16 ok "
	else
		olm_log "    ${FUNCNAME[0]} : relay 16 FAILED aborting"
		return 1
	fi
    olm_setr16 USB 1
    olm_setr16 EQ8 1
    olm_setr16 DEW 1
    olm_setr16 ATK 0
    olm_setr16 FWST 0
    olm_setr16 C14ST 0
    olm_setr16 TSST 0
    olm_setr16 OID 0
    olm_log "  ${FUNCNAME[0]} : exiting"
	return 0
}

olm_off_r16_full(){
    olm_log "    ${FUNCNAME[0]} : shutting down r16"
    delay=1
    olm_setr16 OID 0
    olm_setr16 USB 0
    olm_setr16 EQ8 0
    olm_setr16 DEW 0
    olm_setr16 ATK 0
    olm_setr16 FWST 0
    olm_setr16 C14ST 0
    olm_setr16 TSST 0
    olm_log "    ${FUNCNAME[0]} : r16 shutdown complete"
    rm -f $OLM_R16_SEM
}

olm_off_r8_full(){
    olm_log "    ${FUNCNAME[0]} : starting r16 shutdown"
    olm_setr8 LIGHT 0
    olm_setr8 PILIER 0
    olm_setr8 CAM 0
    olm_setr8 PCN 0
    olm_setr8 PCS 0
    olm_setr8 R16 0
    rm -f $OLM_R8_SEM

    olm_log "    ${FUNCNAME[0]} : r8 shutdown complete"
}

olm_shutdown_indihost(){
    olm_log "    ${FUNCNAME[0]} : shutting down indi host $OLM_IHOST"
    olm_indicmd "sudo shutdown"
}

olm_session_shutdown(){
    olm_log "    ${FUNCNAME[0]} : starting full shutdown"
    olm_shutdown_indihost
    sleep 5
    olm_off_r16_full
    olm_off_r8_full
    olm_log "    ${FUNCNAME[0]} : full shutdown completed"
    touch $OLM_SHUTDOWN_SEM
}

olm_indicmd(){
    olm_log ssh -i $HOME/.ssh/obsm -o ConnectTimeout=5 $OLM_IHOST $*
    ssh -i $HOME/.ssh/obsm -o ConnectTimeout=5 fmeyer@$OLM_IHOST $*
}

olm_fw_get_filter(){ # this is for non indi wheels,
    ping -c 1 -W 1 "$OLM_IHOST" >/dev/null 2>&1
    if test "$?" = "0"; then
        olm_indicmd olm_fw_get
    else
        echo "notup"
    fi
    }

olm_fw_set_filter(){ # this is for non indi wheels,
    ping -c 1 -W 1 "$OLM_IHOST" >/dev/null 2>&1
    if test "$?" = "0"; then
        if test -n "$1"; then
            olm_indicmd fw_set "$1"
        fi
        olm_indicmd olm_fw_get
    else
        echo "notup"
    fi
}

olm_get_indi_status(){
#
# getting indi status running on indi host
#
    ping -c 1 -W 1 $OLM_IHOST >/dev/null 2>&1
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
        ping -c 1 -W 1 $OLM_R16IP >/dev/null 2>&1
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
        ping -c 1 -W 1 ${OLM_R8IP} >/dev/null 2>&1
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

olm_in_sync_eq8_time(){
    # init time
    #
    if test "$1" = "force"; then
        /bin/rm -f "$OLM_EQ8TSYNC"
    fi

    if ! test -f "$OLM_EQ8TSYNC"; then
        /usr/bin/indi_setprop "EQMod Mount.CONNECTION.CONNECT=On"
        setutc=$(date +"EQMod Mount.TIME_UTC.UTC=%Y-%m-%dT%H:%M:%S;OFFSET=0.00")
        if /usr/bin/indi_setprop "$setutc"; then
            iserverlog "set EQ8 UTC : $setutc"
            rm -f $OLM_EQ8TNOTSYNC
            touch $OLM_EQ8TSYNC
        else
            rm -f $OLM_EQ8TSYNC
            touch $OLM_EQ8TNOTSYNC
        fi
    fi
}

olm_in_dname(){
    case $1 in
        indiserver|indi_atik_ccd|indi_eqmod_telescope|indi_qhy_ccd|indi_atik_wheel|indi_canon_ccd|indi_playerone_wheel|indi_playerone_ccd)
            driver=$1;;
        atik) driver=indi_atik_ccd;;
        p1) driver=indi_playerone_ccd;;
        eq8) driver=indi_eqmod_telescope;;
        qhy) driver=indi_qhy_ccd;;
        fw) driver=indi_playerone_wheel;;
        eos) driver=indi_canon_ccd;;
        asi) driver=indi_asi_ccd;;
        *) driver="";;
    esac
    export driver
    }

olm_in_killserv(){
    echo killing server $(cat $OLM_ISERVPIDFILE) |tee -a $OLM_ISERVER_LOG
    kill $(cat "$OLM_ISERVPIDFILE")
    rm $OLM_ISERVPIDFILE
    }

olm_in_killdrivers(){
    while read driver; do
        [[ $driver =~ ^# ]] ||
        olm_in_stop $driver
    done <$OLM_ILOCALDRIVERS
    }

olm_in_start(){
    olm_in_dname $1
    iserverlog "${FUNCNAME[0]} $driver ($1)"
    if test "$driver" = "indiserver"; then
        iserverlog "${FUNCNAME[0]} server, $driver ($1)"
        nohup /usr/bin/indiserver -f $OLM_IFIFO >> $OLM_ISERVER_LOG 2>&1 &
    else
        pid=$(pidof $driver)
        if ! test "$?" = 0; then
            echo start $driver |tee -a $OLM_IFIFO
            driverpid=$(pidof $driver)
            echo $driver running : $driverpid |tee -a $OLM_ISERVER_LOG
            echo -n "$driverpid " >> $OLM_IRUN/$driver.pid
        else
            echo existing driver $driver pid $pid
        fi
    fi
    }

olm_in_pidof(){
    olm_in_dname $1
    if [[ "$driver" == "" ]]; then
        echo
    else
        pid=$(pidof -x $driver -o %PPID)
        if [ "$?" = "0" ]; then
            echo  $pid >$OLM_IRUN/$driver.pid
            iserverlog "  $driver ($1) pid $pid"
            if [[ "$2" == "" ]]; then
                echo $1 $pid
            fi
        else
            iserverlog "  $driver not_running ($1)"
            echo $1 not_running
            if test -f $OLM_IRUN/$driver.pid; then
                rm -f $OLM_IRUN/$driver.pid
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
    iserverlog "${FUNCNAME[0]}"
    echo -n "server "
    olm_in_status indiserver
    while read driver; do
        [[ $driver =~ ^# ]] ||
        (echo -n "$driver " && olm_in_status $driver)
    done <$OLM_ILOCALDRIVERS
    iserverlog "/${FUNCNAME[0]}"
    }

olm_in_start_all(){
    iserverlog ${FUNCNAME[0]}
    iserverlog Starting drivers
    while read driver; do
        [[ $driver =~ ^# ]] ||
        olm_in_start $driver
    done <$OLM_ILOCALDRIVERS
    iserverlog /$FUNCNAME{0}
    }

olm_in_stop_all(){
    iserverlog ${FUNCNAME[0]}
    iserverlog Stopping all drivers
    while read driver; do
        [[ $driver =~ ^# ]] ||
        olm_in_stop $driver
    done <$OLM_ILOCALDRIVERS
    iserverlog Stopping indiserver
    olm_in_killserv
    iserverlog Done /${FUNCNAME[0]}
    }

olm_in_stop(){
    olm_in_dname $1
    iserverlog "${FUNCNAME[0]} $driver ($1)"
    if [[ $driver == "atikextfw" ]]; then # this is for non indi stuff,
        #
        # non-INDI processes here :
        kill -SIGINT $(pidof -x indigo_server -o %PPID)
    else
        #
        # INDI drivers here, including server :
        if [[ $driver == "indiserver" ]]; then
            olm_in_stop_all
        else
            iserverlog stopping $driver
            echo stop $driver |tee $OLM_IFIFO
        fi
    fi
    iserverlog /${FUNCNAME[0]}
    }

olm_in_cycle(){
    olm_in_dname $1
    iserverlog "${FUNCNAME[0]} $driver ($1)"
    if [[ $1 == "indiserver" ]]; then
        iserverlog Cycling indiserver
        olm_in_stop_all
        olm_in_start indiserver
        sleep 1
        olm_in_start_all
    else
        olm_in_stop $driver
        iserverlog "sleeping 1s"
        sleep 1
        olm_in_start $driver
    fi
    iserverlog END CYCLE /${FUNCNAME[0]}
    }

olm_fw_set(){ # this is for non indi wheels,
    echo "# fw_set not implemented, see playerone server"
    return
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

olm_fw_get(){ # this is for non indi wheels,
    echo "# fw_get not implemented, see playerone server"
    return
    cat $olm_fw_statefile
}

olm_fw_start(){ # this is for non indi wheels,

    # nohup $OLM_IROOT/fw.py daemon >/dev/null 2>&1 &
    return
}

olm_fw_stop(){ # this is for non indi wheels,
    # echo STOP >$olm_fw_fifoname
    return
    killall indi_playerone_wheel
}

olm_fw_pwrstepper(){ # this is for non indi wheels,
    case "$1" in
        "ON")
            wget -O /dev/null http://$OLM_R16IP/30/01
            ;;
        "OFF")
            wget -O /dev/null http://$OLM_R16IP/30/00
            ;;
    esac
}


export fsbase="/sys/class/gpio"
traveltime=10
export bat1=171
export bat2=172
export cov1=173
export cov2=174
export pinlist="$bat1 $bat2 $cov1 $cov2"

glist (){
    for pin in $pinlist; do
        echo -n "  $pin : "
        cat $fsbase/gpio$pin/value
    done
}

gstatus(){
    gtest bat > $OLM_BATSTATUS
    gtest cov >>$OLM_BATSTATUS
}

ack(){
    gack cov
    gack bat
    }

ackcov(){
    gack cov
}

ackbat(){
    gack bat
}

gack(){
    p1=$(eval echo \$${1}1)
    p2=$(eval echo \$${1}2)
    gclr $p1
    gclr $p2
    gstatus
}

gtest(){
    if test -z "$1"; then
        gstatus
        return
    fi
    p1=$(eval echo \$${1}1)
    p2=$(eval echo \$${1}2)

    read a <$fsbase/gpio$p1/value
    if test "$a" = "1"; then
        echo -n "1 "
        return 1
    fi

    read a <$fsbase/gpio$p2/value
    if test "$a" = "1"; then
        echo -n "1 "
        return 1
    fi
    echo -n "0 "
    return 0
}

gclr (){
    pin=$fsbase/gpio$1
    echo 0 |sudo tee $pin/value >/dev/null
}

gset (){
    pin=$fsbase/gpio$1
    echo 1 |sudo tee $pin/value >/dev/null
    glist
}

gstop(){
    stopcov
    stopbat
}

closecov(){
    gtest bat
    if test "$?" = "0"; then
        gclr $cov1 >/dev/null 2>&1
        gset $cov2 >/dev/null 2>&1
        nohup sleep $traveltime  >/dev/null 2>&1 && gset $cov1 && gstatus >/dev/null & >/dev/null 2>&1
    else
        echo "bat not safe, not closing cov"
    fi
    gstatus
}

stopcov(){
    killall sleep
    sleep .5
    gset $cov1 >/dev/null 2>&1
    gset $cov2 >/dev/null 2>&1
    gstatus
}

opencov(){
    if test "$?" = 0; then
        gset $cov1 >/dev/null 2>&1
        gclr $cov2 >/dev/null 2>&1
        nohup sleep $traveltime >/dev/null 2>&1  && gclr $cov1 && gstatus >/dev/null & >/dev/null 2>&1
    else
        echo "bat not safe, not opening cov"
    fi
}

closebat(){
    gtest cov
    if test "$?" = 0; then
        gclr $bat1 >/dev/null 2>&1
        gset $bat2 >/dev/null 2>&1
        nohup sleep $traveltime >/dev/null 2>&1 && gset $bat1 && gstatus >/dev/null & >/dev/null 2>&1
    else
        echo "cov not safe, not closing bat"
    fi
    gstatus
}

stopbat(){
    killall sleep
    sleep .5
    gset $bat1 >/dev/null 2>&1
    gset $bat2 >/dev/null 2>&1
    gstatus
}

openbat(){
    gtest cov
    if test "$?" = 0; then
        gset $bat1 >/dev/null 2>&1
        gclr $bat2  >/dev/null 2>&1
        nohup sleep $traveltime >/dev/null 2>&1 && gclr $bat1 && gstatus >/dev/null & >/dev/null 2>&1
    else
        echo "cov not safe, not opening bat"
    fi
    gstatus
}

export gset gclr glist oppenbat opencov clrcov

covinit(){
for i in $pinlist; do
    pin=$fsbase/gpio"$i"
    if ! test -d $pin; then
        echo $i |sudo tee -a $fsbase/export
        echo out |sudo tee -a $pin/direction
        echo $pin ready
    else
        echo $pin already ready
    fi
done
}

if ! test -d $fsbase/gpio"$bat1"; then
    covinit
fi

if test -n "$1"; then
	command="$1"
	shift
    $command $*
fi
