#source /etc/bash_completion.d/siril-completion
export SIRILRC="$HOME/.config/siril/sirilrc" # location of the siril bash cli resource file
source $SIRILRC
#
# Cosmétique (couleur, formattage...)
#
V="\\033[1;32m"
N="\\033[0;39m"
R="\\033[1;31m"
C="\\033[1;36m"
B="\\033[1;31;5m"

green(){
    set -o noglob
    echo -ne "$V   " $1; echo -e "  $N$2" >&2
    set +o noglob
    }

red(){
    set -o noglob
    echo -ne "$R   " $1; echo -e "  $N$2" >&2
    set +o noglob
    }

cyan(){
    set -o noglob
    echo -ne "$C   " $1; echo -e "  $N$2" >&2
    set +o noglob
    }

blink(){
    set -o noglob
    echo -ne "$B$C   " $1; echo -e "  $N$2" >&2
    set +o noglob
    }

splog(){ # log to stderr
    set -o noglob
    echo $* >&2
    set +o noglob
}


# User-defined nomenclature and separators
declare -A config
declare -A extract
config[nomenclature]="obj-filter-exposure-binning_timestamp"
config[separators]="- _"

srl_getseqfile (){
    local input="$1"
    local srlwd="${SRLWD:-.}"  # Default to current directory if $SRLWD is not set
    if test -z "$1"; then
        echo "srl_getseqfile needs a seq name" >&2
        return 1
    fi

    # Check if $input ends with .seq and if the file exists
    if [[ "$input" == *.seq && -f "$srlwd/$input" ]]; then
        echo "$srlwd/$input"
        return 0
    fi

    # Check if $input.seq exists
    if [[ -f "$srlwd/$input.seq" ]]; then
        echo "$srlwd/$input.seq"
        return 0
    fi

    # Check if $input_.seq exists
    if [[ -f "$srlwd/${input}_.seq" ]]; then
        echo "$srlwd/${input}_.seq"
        return 0
    fi

    # If none of the conditions match, return the original input
    echo "No such seq $1[_.seq]" >&2
    return 1
}

srl_filecount() {
    # list files whose name match the sequence name 
    ls $SRLWD/$1*.fits* |wc -l
}


srl_seqsize() {
    seqfile=$(srl_getseqfile $1)
    read dumb name start nb dumb <<<$(grep '^S' $seqfile) 
    echo $nb
}

# Function to extract fields from a filename
srl_getfields() {
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
    shopt -s nocasematch;
    if [[ ${extract[obj]} =~ ^(bias|biases|offset) ]]; then
        extract[type]="bias"
        extract[obj]="bias"
        else if [[ ${extract[obj]} =~ ^(dark) ]]; then
            extract[obj]="dark"
            extract[type]="dark"
            else if [[ ${extract[obj]} =~ ^(flat) ]]; then
                extract[obj]="flat"
                extract[type]="flat"
            else
                extract[type]="light"
            fi
        fi
    fi
    shopt -u nocasematch;
}

srl_guesstype(){
    shopt -s nocasematch;
    if [[ ${1} =~ ^(bias|biases|offset) ]]; then
        echo "Bias"
        shopt -u nocasematch;
        return 0
    fi

    if [[ ${1} =~ ^(dark) ]]; then
        echo "Dark"
        shopt -u nocasematch;
        return 0
    fi

    if [[ ${1} =~ ^(flat) ]]; then
        echo "Flat"
        shopt -u nocasematch;
        return 0
    fi
    echo "Light"
    shopt -u nocasematch;
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
    if test -n "$1"; then
        SRLWD=$1
    fi

    if test -z "$SRLWD"; then
        SRLWD=$(pwd)
    else
        if ! test -d "$SRLWD"; then
            echo "$SRLWD not a directory">&2
            return 1
        else
            SRLWD=$(realpath $SRLWD)
        fi
    fi
    siril -s - <<ENDSIRIL >$SIRLOG/logsiril 2>&1
cd $SRLWD
chkseq
ENDSIRIL
echo Checking $seqs sequences in $SRLWD: >&2
ls -w1 $SRLWD/*.seq |grep -i "$regex" 2>/dev/null |sed 's/^/	/' |xargs -I@ -n1 basename @ .seq
if ! test "$?" = "0"; then
    echo "No sequence found in dir $SRLWD" >&2
fi
}

srl_getwidth(){
    fitsheader $SRLWD/$1 |grep NAXIS1 |awk -F'[=/]' '{print $2}' 
}


srl_downsample(){
    if test -f "$1"; then
        file=$1
        if ! test ${1:0:1} = '/'; then
            file=$PWD/"$1";
        fi
        siril -s - <<ENDSIRIL >$SIRLOG/logsiril 2>&1
load $file
resample -height=2088
crop 0 0 3124 2088
save $file
ENDSIRIL
    fi
    }

srl_oversample(){
    if test -f "$1"; then
        file=$1
        if ! test ${1:0:1} = '/'; then
            file=$PWD/"$1";
        fi
        siril -s - <<ENDSIRIL >$SIRLOG/logsiril 2>&1
load $file
resample -width=6252
crop 0 0 6252 4176
save $file
ENDSIRIL
    fi
    }

srl_config(){
    echo $0
}

srl_getobj(){
    srl_getfields $1
    echo ${extract[obj]}
}

srl_getfilter(){
    srl_getfields $1
    echo ${extract[filter]}
}

srl_lscal(){
    find $SRLWD -iname "[dark|flat|bias|offset]*.seq" |xargs -I@ basename @ _.seq 
}

srl_pplist(){
    echo $1
}

srl_mkmaster(){
    shopt -u nocasematch;
    # arg 1 : sequence name
    # arg 2 : (optional) master output file name
    # -a : archive file in $SRLCAL
    # -f : force overwriting of file in $SRLCAL if it already exists
    #
    archive=""
    #
    #
    # Arg processing :
    #
    set -- $(getopt "af" "$@")
    # Sets positional parameters to command-line arguments.
    while [ ! -z "${1}" ]
    do
        case "${1}" in
            -a) archive='y';; 
            -f) archive='Y';;
            *) break;;
        esac
        shift
    done
    shift

    base=${1}
    inputbase=$SRLWD/${1}
    if test -f ${inputbase}_.seq; then
        seqname="${inputbase}"_.seq
    else
        if test -f ${inputbase}.seq; then
            seqname="$inputbase".seq
        else 
            splog "Error: No sequence $seqname\* found" 
            return 1
        fi
    fi

    IFS=_ read cname stamp <<<$(echo $base) # separates canonical name from whatever lies after the first '_'
    mastername="$2"
    if test -z "$mastername"; then # no master name provided
        IFS=- read typ filter exposure bin dum <<<$(echo $cname)
        imgtyp=$(srl_guesstype $typ )
        echo "$typ @ $filter @ imgtyp @$imgtyp@"
        case "$imgtyp" in
            "Bias")
                norm=nonorm
                mastername="MasterBias-$bin${SRLSFX[0]}";;
            "Dark")
                norm=nonorm
                mastername="MasterDark-$exposure-$bin${SRLSFX[0]}";;
            "Flat")
                norm=mul
                mastername="MasterFlat-$filter-$bin${SRLSFX[0]}";;

            *)
                echo "Unkown frame type @$imgtyp@, not stacking"
                return 1;;
        esac
    fi
    green "Making master $imgtyp from $seqname -> $mastername"
    siril -s - <<ENDMKMASTER >$SIRLOG/logsiril 2>&1
cd $SRLWD
stack $seqname rej 3 3 -norm=$norm -out=$mastername
ENDMKMASTER
    ls -l $SRLWD/$mastername
    destfile=${SRLCAL}/$mastername

    if test -z "$archive"; then
        green "archive $mastername to $SRLCAL ?"
        splog "(y to archive, Y to overwrite existing)"
        read archive
    fi


    case "$archive" in
        "y")
            if test -f "$destfile"; then # dest file exists
                red "$destfile exists"
                if [[ $- == *i* ]]; then # interactive, ask confirmation to overwrite
                    echo -n 'overwrite (y/N) ? '
                    read answer
                    if [[ ${answer} == 'y' ||  ${answer} == 'Y' ]]; then
                        cp -p $mastername $SRLCAL/${destfile}
                    fi
                else
                    echo 'Not overwriting. -f to force overwrite'
                fi
            else
                splog "Copying $mastername to $SRLCAL"
                cp -p $mastername $SRLCAL/$mastername
            fi
            ;;

        "Y")
            splog "Copying $mastername to $SRLCAL"
            cp -p $mastername $SRLCAL/$mastername
            ;;
        *)
            green -n "archive $mastername in $SRLCAL ? "
    esac
    return 0
}

srl_wd(){
    if test -n "$1"; then
        if test -d "$1"; then
            realdir=$(readlink -f $1)

            export SRLWD="$realdir"
            if ! test -f $SIRILRC; then
                echo export SRLWD=$realdir >$SIRILRC;
            else
                sed  -i 's@\(^export SRLWD=\).*@\1'$realdir'@' $SIRILRC
            fi
        fi
    else
        if test -z "$SRLWD"; then
            export SRLWD=$(pwd)
        else
            echo $SRLWD
        fi
    fi
}

srl_flatcalib(){ # sample call : srl_flatcal A3-Blue-30s-2x2_ Flat-Blue
    logfile=$SRLTMP/${FUNCNAME[0]}.log
    splog "Running ${FUNCNAME[0]}, output to $logfile"
    splog " calibrating $1 with $2 in dir $SRLWD"
    exec 6>&1    # Lie le descripteur de fichier #6 avec stdout.
                 # Sauvegarde stdout.
    #
    exec >$logfile   # stdout remplace par outfile2
    sirilscript=$SRLTMP/flatcalib.ssc
    cd $SRLWD
    echo "cd $SRLWD" >$sirilscript
    seqname="$1"
    masterflat="$2"
    if test -n "$seqname" && test -f "$masterflat"; then
        echo "calibrate ${seqname} -flat=$masterflat" >>$sirilscript
    fi
    siril -s $sirilscript

    srl_chkseq
    exec 1>&6 6<&-
    srl_seqsize pp_$seqname
}

srl_mkflat(){
    logfile=$SRLTMP/${FUNCNAME[0]}.log
    splog "Running ${FUNCNAME[0]}, output to $logfile" 
    splog " making flats in dir $SRLWD"
    exec 6>&1    # Lie le descripteur de fichier #6 avec stdout.
                 # Sauvegarde stdout.
    #
    exec >$logfile   # stdout remplace par outfile2

    sirilscript=$SRLTMP/flat.ssc
    rootdir=$1
    if test -z "$rootdir"; then
        rootdir=$SRLWD
        if test -z "$rootdir"; then
            rootdir=$(pwd)
        fi
    fi
    cd ${rootdir}

    splog " building siril script $sirilscript" >&2
    echo "cd $rootdir" >$sirilscript
    seqname=()
    for i in Flat-*.seq; do
        seq=$(basename $i .seq)
        seqname+=($seq)
        echo "stack ${seq} rej 3 3 -norm=mul"
    done >>$sirilscript;

    siril -s $sirilscript
    builtlist=""
    mkdir -p archives
    for i in Flat-*.seq; do
        seqroot=$(basename $i .seq)
        destmaster=$(echo $i | awk -F\- '{print $1 "-" $2}').fits
        builtlist="$builtlist "$destmaster
        mv $rootdir/${seqroot}stacked.fits ${destmaster}
    done
    /bin/ls -l $builtlist >&2
    exec 1>&6 6<&-
}

