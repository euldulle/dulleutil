# !/bin/bash
#
#
OBSLM=/home/fmeyer/observatoire_moutherot/
wd=$OBSLM/relay_server/tmp

arg="$1"
if test "$1" = ""; then
    # echo will do 16 by default
    arg="16"
fi

if test "$arg" = "16"; then
    outfile="$wd/relay16"
    failed=""
    ping -c 1 -W 1 relais16 >/dev/null 2>&1
    if test "$?" = "0"; then
        echo OK
        for i in $(seq 0 3); do
            rm -rf $outfile-$i
            wget relais16/30/43 --timeout=1 --tries=2 -O $outfile-$i
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
    ping -c 1 -W 1 relais8 >/dev/null 2>&1
    if test "$?" = "0"; then
        echo OK
        /usr/bin/wget -O $outfile http://fmeyer:4so4xRg9@relais8:2380/relays.cgi --timeout=2 --tries=2 2>/dev/null
        if test "$?" = "0"; then
            cat "$outfile" |grep ': '|sed -E 's/ *[^ ]+ *//'
        else
            echo notup
        fi
    else
        echo notup
    fi
fi


#   cat <<END
#   <tr><td title="17"> Switch Light</td><td> <small><a href="http://$1/page/relays.py?switch='http://relais8:2380/relays.cgi?relay=1'>Switch light</a></td></tr>
#   END
