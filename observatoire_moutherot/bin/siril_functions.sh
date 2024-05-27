#!/bin/bash
#
export SIRROOT="/data/astrolab"
export SIRBIN="$SIRROOT/bin"
export SIRCALIB="$SIRROOT/Poseidon_ccd"
export SIRTMP="$SIRROOT/tmp"
export SIRLOG="$SIRROOT/log"
export PATH="$SIRBIN:$PATH"
source ~/git/dulleutil/observatoire_moutherot/bin/siril-completion

srl_guesstype(){
    shopt -s nocasematch;
    if [[ ${1} =~ ^(bias|biases|offset) ]]; then
        echo "Bias"
        return 0
    fi

    if [[ ${1} =~ ^(dark) ]]; then
        echo "Dark"
        return 0
    fi

    if [[ ${1} =~ ^(flat) ]]; then
        echo "Flat"
        return 0
    fi
    echo "Light"
    return 1
}

srl_chkseq(){
    let count=0
    regex=""
    seqs="all"
    local OPTIND opt

    while getopts "fdb" opt; do
      case $opt in
        f)
          # flats of any flavor
          regex="/flats*"
          seqs="flat"
          let count=$count+1
          ;;
        d)
          # darks
          regex="/darks*"
          seqs="dark"
          let count=$count+1
          ;;
        b)
          # bias
          regex="/bias(es)*|offsets*"
          seqs="bias/offset"
          let count=$count+1
          ;;
      esac
    done

    if test "$count" -gt "1"; then
        echo "Error: only one of -d -f -b is allowed" >&2
        return 1
    fi

    shift $((OPTIND-1))
    rootdir=$1

    if test -z "$rootdir"; then
        rootdir=$(pwd)
    else
        if ! test -d "$rootdir"; then
            echo "$rootdir not a directory">&2
            return 1
        else
            rootdir=$(realpath $rootdir)
        fi
    fi
    siril -s - <<ENDSIRIL >$SIRLOG/logsiril 2>&1
cd $rootdir
chkseq
ENDSIRIL
echo Checking $seqs sequences in $rootdir: >&2
ls -w1 $rootdir/*.seq |grep -i "$regex" 2>/dev/null |sed 's/^/	/'
if ! test "$?" = "0"; then
    echo "No sequence found in dir $rootdir" >&2
fi
}
export chkseq

srl_mkmaster(){
    if test -z "$rootdir"; then
        rootdir=$(pwd)
    fi

    seqname="$1"
    IFS=_ read cname stamp <<<$(echo $seqname) # separates canonical name from whatever lies after the first '_'
    mastername="$2"
    if test -z "$mastername"; then # no master name provided
        IFS=- read typ filter exposure bin dum <<<$(echo $cname)
        imgtyp=$(srl_guesstype $typ )
        echo "$typ @ $filter @ imgtyp @$imgtyp@"
        case "$imgtyp" in
            "Bias")
                mastername="MasterBias-$bin";;
            "Dark")
                mastername="MasterDark-$exposure-$bin";;
            "Flat")
                mastername="MasterFlat-$filter-$bin";;
            *)
                echo "Unkown frame type @$imgtyp@, not stacking"
                return 1;;
        esac
    fi

    siril -s - <<ENDMKMASTER
        cd $rootdir
        stack $seqname rej 3 3 -norm=mul -out=$mastername
ENDMKMASTER
    return 0
}

mkflat(){
    sirilscript=$SIRTMP/flat.ssc
    rootdir=$1
    if test -z "$rootdir"; then
        rootdir=$(pwd)
    fi
    cd ${rootdir}

    echo "cd $rootdir" >$sirilscript
    seqname=()
    for i in Flat-*.seq; do
        seq=$(basename $i .seq)
        seqname+=($seq)
        echo "stack ${seq} rej 3 3 -norm=mul"
    done >>$sirilscript;

    siril -s $sirilscript
    for i in Flat-*.seq; do
        mv $rootdir/${i}_stacked.fits $(echo $i | awk -F\- '{print $1 "-" $2}').fits
        mv $rootdir/$(basename ${i} .seq)* $calibdir/archives/
    done
}
