#!/bin/bash
back=0
while [ 1 ]; 
do
ncal -3bM $(date -d "$back month ago" +"%m %Y") $*
 stty cbreak -echo
 char=$(timeout --foreground 3600 dd if=/dev/tty bs=1 count=1 2>/dev/null)
# char=$(dd if=/dev/tty bs=1 count=1 2>/dev/null)
 stty -cbreak echo
 case $char in
    -) (( ++back ));; # on recule d'un mois
    +) (( --back ));; # on avance d'un mois
    0) (( back=0 ));; # on revient auj'deu
 esac
done
