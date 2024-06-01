#!/bin/bash
#
#
#
source /etc/bash_completion.d/siril-completion

# User-defined nomenclature and separators
declare -A config
declare -A extract
config[nomenclature]="object-filter-exposure-binning_timestamp"
config[separators]="- _"

# Function to extract fields from a filename
extract_fields() {
    local filename=$(basename "$1")
    
    # Remove all extensions from the filename
    while [[ $filename =~ \.[^.]+$ ]]; do
        filename=${filename%.*}
    done
    
    local nomenclature=${config[nomenclature]}
    local separators=${config[separators]}

    # Extract the field names into an array
    IFS='-' read -ra fields <<< "${nomenclature//[_@]/-}"

    # Extract the objectname field (first field)
    local first_sep=${separators:0:1}
    local objectname="${filename%%$first_sep*}"
    local remaining_filename="${filename#*$first_sep}"

    # Replace the separators in the remaining filename with spaces
    local sep_pattern=$(echo $separators | sed 's/ /|/g')
    IFS=' ' read -ra field_values <<< "$(echo "$remaining_filename" | sed -E "s/($sep_pattern)/ /g")"
    
    # Add the objectname to the field values
    field_values=("$objectname" "${field_values[@]}")

    # Check if the number of fields matches the number of values
    if [ ${#fields[@]} -ne ${#field_values[@]} ]; then
        echo "Error: Number of fields and values do not match."
        return 1
    fi

    # Create an associative array to store the field values
    for i in "${!fields[@]}"; do
        extract[${fields[$i]}]=${field_values[$i]}
    done
}

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

srl_getobjname(){
    echo $1 |awk -F- '{print $1}'
}

srl_pplist(){
    echo $1
}

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

export SRL="/data/astrolab"
export SRLBIN="$SRLROOT/bin"
export SRLCAL="$SRLROOT/Poseidon_ccd"
export SRLTMP="$SRLROOT/tmp"
export SRLLOG="$SRLROOT/log"
export PATH="$SRLBIN:$PATH"

