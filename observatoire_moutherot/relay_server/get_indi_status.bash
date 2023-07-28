#!/bin/bash
#
# getting indi status running on oid
#
source /home/fmeyer/.ssh/environment >/dev/null 2>&1
ping -c 1 -W 1 oid >/dev/null 2>&1
if test "$?" = "0"; then
    echo OK
    ssh oid in_status_all
else
    echo notup
fi
