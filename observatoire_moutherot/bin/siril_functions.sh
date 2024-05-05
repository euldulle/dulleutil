#!/bin/bash
#
export SIRROOT="/data/astrolab"
export SIRBIN="$SIRROOT/bin"
export SIRCALIB="$SIRROOT/Poseidon_ccd"
export SIRTMP="$SIRROOT/tmp"
export SIRLOG="$SIRROOT/log"
export PATH="$SIRBIN:$PATH"

chkseq(){
    rootdir=$1
    if test -z "$rootdir"; then
        rootdir=$(pwd)
    else
        rootdir=$(realpath $rootdir)
    fi
    siril -s - <<ENDSIRIL >$SIRLOG/logsiril 2>&1
cd $rootdir
chkseq
ENDSIRIL
echo Checking sequences in $rootdir: >&2
cd $rootdir
ls -w1 *.seq 2>/dev/null
if ! test "$?" = "0"; then
    echo "No sequence found in dir $rootdir" >&2
fi
}
export chkseq

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
