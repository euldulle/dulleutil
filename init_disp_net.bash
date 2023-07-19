#!/bin/bash
home="/home/fmeyer"
#
# no fucking bell
xset b off
# keyboard delay and rate
xset r rate 200 120

if (lsusb -v |grep 000800110115030); then
    #
    # mouth
    #
    autorandr $home/bin/mto-autorandr
    /usr/bin/nmcli con down 03-obs_eth0
    /usr/bin/nmcli con up ltfb
    nohup xmessage -nearmouse " Réseau Moutherot " -timeout 2 >/dev/null 2>&1 &
    autotunnels
    sshu start
    exit
fi
if (sudo lsusb -v |grep 0dac4faf-8700-ee40-b758-26a107d76c6b >/dev/null 2>&1); then
    #
    # observatoire
    #
    autorandr $home/bin/obs-autorandr
    /usr/bin/nmcli radio wifi off
    /usr/bin/nmcli con up  obs-ethusb
    sudo mount /mars
    source /raid0/bin/tf_functions.sh
    nohup xmessage -nearmouse " Réseau Obs " -timeout 2 >/dev/null 2>&1 &
    exit
fi
#
# other
#
nohup xmessage -nearmouse " Réseau inconnu " -timeout 2 >/dev/null 2>&1 &
#
# Throttling sshuttle up:
#
$home/bin/sshu start
