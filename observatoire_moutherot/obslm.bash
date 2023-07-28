export OLM_R8_SEM="/tmp/olm_r8_sem"
export OLM_R16_SEM="/tmp/olm_r16_sem"

function setr8-usage(){
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

function setr16-usage(){
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

function olm-setr8(){
    baserel='http://fmeyer:4so4xRg9@relais8:2380/relays.cgi?relay='

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
    echo "# switching $switch, $baserel$addr"

    curl -o /dev/null "$baserel"$addr  >/dev/null 2>/dev/null
}

function olm-setr16(){
    baserel='http://192.168.0.28/30/'

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
    echo "# setting $switch to $ad, $baserel$addr"

    curl -o /dev/null "$baserel"$addr  >/dev/null 2>/dev/null
}

function olm-cold_init(){
    olm-init_r8_full
    olm-init_r16_full
    }

function olm-init_r8_full(){
    delay=1
    olm-setr8 PILIER 1
    sleep $delay
    olm-setr8 CAM 1
    sleep $delay
    olm-setr8 PCN 1
    sleep $delay
    olm-setr8 PCS 1
    sleep $delay
    olm-setr8 R16 1
    }

function olm-init_r16_full(){
    delay=2
    olm-setr16 USB 1
    sleep $delay
    olm-setr16 EQ8 1
    sleep $delay
    olm-setr16 DEW 1
    sleep $delay
    olm-setr16 ATK 1
    sleep $delay
    olm-setr16 FWST 1
    sleep $delay
    olm-setr16 C14ST 1
    sleep $delay
    olm-setr16 TSST 1
    sleep $delay
    olm-setr16 OID 1
}

function olm-off_r16_full(){
    delay=1
    olm-setr16 OID 0
    sleep $delay
    olm-setr16 USB 0
    sleep $delay
    olm-setr16 EQ8 0
    sleep $delay
    olm-setr16 DEW 0
    sleep $delay
    olm-setr16 ATK 0
    sleep $delay
    olm-setr16 FWST 0
    sleep $delay
    olm-setr16 C14ST 0
    sleep $delay
    olm-setr16 TSST 0
}
