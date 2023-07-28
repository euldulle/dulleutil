#!/bin/bash
#
# getting indi status running on oid
# 
#  (plus ou moins redondant voire inutile, 
#   l'utilisation directe des ssh oid fw_get ou fw_set est aussi efficace)
source /home/fmeyer/.ssh/environment

ping -c 1 -W 1 oid >/dev/null 2>&1
if test "$?" = "0"; then
    case "$0" in
        "get_fw_status")
            ssh oid fw_get
            ;;
        "set_fw_status")
            if test -n "$1"; then
                ssh oid fw_set "$1"
            fi
            ;;
    esac
    ssh oid fw_get
else
    echo "notup"
fi
