export OLM_ROOT="/home/fmeyer/observatoire_moutherot"
export OLM_LOGDIR="$OLM_ROOT/log"
export OLM_LOG="$OLM_LOGDIR/olm.log"
export OLM_DAEMONLOG="$OLM_LOGDIR/relayd.log"
export OLM_SERVERLOG="$OLM_LOGDIR/relayserver.log"
export OLM_R8_SEM="/tmp/olm_r8_sem"
export OLM_R16_SEM="/tmp/olm_r16_sem"
export OLM_EQ8TSYNC="/tmp/eq8tsynced"

export OLM_RELAY8IP="192.168.0.23"
export OLM_RELAY8PORT="2380"
export OLM_BASER8="http://fmeyer:4so4xRg9@${OLM_RELAY8IP}:${OLM_RELAY8PORT}/relays.cgi"

export OLM_RELAY16IP="192.168.0.28"
export OLM_RELAY8PORT=""
export OLM_BASER16="http://${OLM_RELAY16IP}/30"

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
    OID       odroid oid
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
    echo "arg $1"
    switch="$1"
    if test -z "$switch"; then
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
    olm_log "     ${FUNCNAME[0]}: switching $switch, ${OLM_BASER8}?relay=$addr"

    curl -o /dev/null "${OLM_BASER8}?relay="$addr  >/dev/null 2>/dev/null
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
    olm_log "     ${FUNCNAME[0]}: setting $switch to $ad, ${OLM_BASER16} $addr"

    curl -o /dev/null "${OLM_BASER16}/"$addr  >/dev/null 2>/dev/null
}

olm_cold_init(){
    olm_log "  ${FUNCNAME[0]} : starting init sequence"
    olm_init_r8_full
    # allow 15 s for relay16 to come up :
    curl --connect-timeout 15 -o /dev/null "${OLM_BASER16}"  >/dev/null 2>/dev/null
    if test "$?" ="0"; then
        olm_init_r16_full
    else
        olm_log "${FUNCNAME[0]} : error connecting r16, not initializing it"
    fi
    olm_log "  ${FUNCNAME[0]} : init over"
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
    delay=2
    olm_setr16 USB 1
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
    olm_log "    ${FUNCNAME[0]} : starting r16 shutdown"
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

olm_fullshutdown(){ 
    olm_log "    ${FUNCNAME[0]} : starting full shutdown"
    olm_shutdown_oid
    sleep 5
    olm_off_r16_full 
    olm_off_r8_full
    olm_log "    ${FUNCNAME[0]} : full shutdown completed"
}

olm_fw_get_filter(){
    target="oid"

    ping -c 1 -W 1 "$target" >/dev/null 2>&1
    if test "$?" = "0"; then
        case "$0" in
            "get_fw_status")
                ssh "$target" fw_get
                ;;
            "set_fw_status")
                if test -n "$1"; then
                    ssh "$target" fw_set "$1"
                fi
                ;;
        esac
        ssh "$target" fw_get
    else
        echo "notup"
    fi
    }

olm_fw_get_filter(){
    target="oid"
    ping -c 1 -W 1 "$target" >/dev/null 2>&1
    if test "$?" = "0"; then
        case "$0" in
            "get_fw_status")
                ssh "$target" fw_get
                ;;
            "set_fw_status")
                if test -n "$1"; then
                    ssh "$target" fw_set "$1"
                fi
                ;;
        esac
        ssh oid fw_get
    else
        echo "notup"
    fi
}

olm_get_indi_status(){
#
# getting indi status running on oid
#
    ping -c 1 -W 1 oid >/dev/null 2>&1
    if test "$?" = "0"; then
        echo OK
        ssh oid in_status_all 
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
        outfile="$wd/relay16"
        failed=""
        ping -c 1 -W 1 $OLM_RELAY16IP >/dev/null 2>&1
        if test "$?" = "0"; then
            echo OK
            for i in $(seq 0 3); do
                rm -rf $outfile-$i
                wget --no-cache ${OLM_BASER16}/43 --timeout=1 --tries=2 -O $outfile-$i >/dev/null 2>&1
                # curl  ${OLM_BASER16}/43 --output $outfile-$i >/dev/null 2>&1
                if ! test "$?" = "0"; then
                    failed="1"
                    break
                fi
            done
            if test "$failed" = ""; then
                cat $outfile-[0-3] \
                    |sed 's/<p>R/<p> R/g;s/<p> R/\n<p> R/g;s@&nbsp@@g' \
                    |grep 'Relay...:' \
                    |sed 's@<center.*@@;s@<small>.*</small>@@;s@> ON/@>ON/@;s@>O@ >O@g;s@</font>@@;s@028@0.28@;s@href=@@;s@"@@g'\
                    |awk '{print $2 " " $5 " " $7}'
            else
                echo notup
            fi
        else
            echo notup
        fi
    fi

    if test "$arg" = "8"; then
        outfile="$wd/relay8"
        ping -c 1 -W 1 ${OLM_RELAY8IP} >/dev/null 2>&1
        if test "$?" = "0"; then
            echo OK
            /usr/bin/wget -O $outfile ${OLM_BASER8} --timeout=2 --tries=2 >/dev/null 2>/dev/null 
            if test "$?" = "0"; then
                cat "$outfile" |grep ': '|sed -E 's/ *[^ ]+ *//'
            else
                echo notup
            fi
        else
            echo notup
        fi
    fi
    }

source /home/fmeyer/.ssh/environment >/dev/null 2>&1
ssh-add /home/fmeyer/.ssh/obsm >/dev/null 2>&1

if test -n "$1"; then
    $*
fi
