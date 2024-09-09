#!/usr/bin/python
import os
import tkinter as tk
import requests
import subprocess
import re
import asyncio
from time import sleep
import paramiko
import relay_rsc
from tkinter import scrolledtext



relays_16 = {
    'Relay-12': {
        'name': ['USB'],
        'url': "",
        'type': "SWITCH",
        'position': 0,
        'button': [],
        'status': "OFF"
        },

    'Relay-13': {
        'name': ['EQ8'],
        'url': "",
        'type': "SWITCH",
        'position': 1,
        'button': [],
        'status': "OFF"
        },

    'Relay-10': {
        'name': ['Oid'],
        'url': "",
        'type': "SWITCH",
        'position': 2,
        'button': [],
        'status': "OFF"
        },

    'Relay-09': {
        'name': ['DH'],
        'url': "",
        'type': "SWITCH",
        'position': 3,
        'button': [],
        'status': "OFF"
        },

    'Relay-11': {
        'name': ['CCD'],
        'url': "",
        'type': "SWITCH",
        'position': 4,
        'button': [],
        'status': "OFF"
        },

    'Relay-01': {
        'name': ['Sfw'],
        'position': 6,
        'type': "SWITCH",
        'url': "",
        'button': [],
        'status': "OFF"
        },

    'Relay-02': {
        'name': ['S14'],
        'url': "",
        'type': "SWITCH",
        'position': 7,
        'button': [],
        'status': "OFF"
        },

    'Relay-03': {
        'name': ['Sts'],
        'url': "",
        'type': "SWITCH",
        'position': 8,
        'button': [],
        'status': "OFF"
        },

    'Relay-04': {
        'name': ['Lpi3'],
        'url': "",
        'type': "SWITCH",
        'position': 9,
        'button': [],
        'status': "OFF"
        },

    'Relay-05': {
        'name': ['Pi3'],
        'url': "",
        'type': "SWITCH",
        'position': 10,
        'button': [],
        'status': "OFF"
        },

    'Relay-14': {
        'name': ['Clo'],
        'url': "",
        'type': "TEMP",
        'position': 12,
        'button': [],
        'status': "OFF"
        },

    'Relay-15': {
        'name': ['Stp'],
        'url': "",
        'type': "TEMP",
        'position': 13,
        'button': [],
        'status': "OFF"
        },

    'Relay-16': {
        'name': ['Opn'],
        'url': "",
        'type': "TEMP",
        'position': 14,
        'button': [],
        'status': "OFF"
        }
    }

relays_8 = {
    'Relay1': {
        'name': ['lgt'],
        'position': 5,
        'button': [],
        'addr': 1,
        'status': "OFF",
        'config': "NO" # normally open
        },

    'Relay2': {
        'name': ['pil'],
        'position': 0,
        'button': [],
        'addr': 2,
        'status': "ON",
        'config': "NC" # normally closed
        },

    'Relay3': {
        'name': ['cam'],
        'position': 3,
        'button': [],
        'addr': 3,
        'status': "OFF",
        'config': "NO" # normally open
        },

    'Relay4': {
        'name': ['PrN'],
        'position': 4,
        'button': [],
        'addr': 4,
        'status': "ON",
        'config': "NC" # normally closed
        },

    'Relay5': {
        'name': ['PrS'],
        'position': 2,
        'button': [],
        'addr': 5,
        'status': "ON",
        'config': "NC" # normally closed
        },

    'Relay6': {
        'name': ['R16'],
        'position': 1,
        'button': [],
        'addr': 6,
        'status': "ON",
        'config': "NC" # normally closed
        },

    'Relay7': {
        'name': ['CCD'],
        'position': -1,
        'button': [],
        'addr': 7,
        'status': "OFF"
        },

    'Relay8': {
        'name': ['CCD'],
        'position': -1,
        'button': [],
        'addr': 8,
        'status': "OFF"
        }
    }


cmds = {
    'synceq8': {
        'name': ['SyncEQ8'],
        'position': 1,
        'button': [],
        'cmd': ["olm_in_sync_eq8_time"],
        'status': -1,
        'remote': True,
        'confirm': False
        },

    'movecover': {
        'name': ['Cover1','Cover0'],
        'position': 2,
        'button': [],
        'cmd': ['closecov','opencov'],
        'status': 0,
        'states': ["OPENED", "CLOSED"],
        'remote': True,
        'confirm': False
        },

    'movebath': {
        'name': ['Bath1','Bath0'],
        'position': 3,
        'button': [],
        'cmd': ['closebat','openbat'],
        'status': 0,
        'statesname': ["OPENED", "CLOSED"],
        'remote': True,
        'confirm': False
        },

    'cycle qhy': {
        'name': ['QHYCyc'],
        'position': 4,
        'button': [],
        'cmd': ['olm_in_cycle qhy'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle eq8': {
        'name': ['EQ8Cyc'],
        'position': 5,
        'button': [],
        'cmd': ['olm_in_cycle eq8'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle ccd': {
        'name': ['CCDcyc'],
        'position': 6,
        'button': [],
        'cmd': ['olm_in_cycle p1'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle fw': {
        'name': ['fwCyc'],
        'position': 7,
        'button': [],
        'cmd': ['olm_in_cycle fw'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle indi': {
        'name': ['indiCyc'],
        'position': 8,
        'button': [],
        'cmd': ['olm_in_cycle indiserver'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'Reboot oid': {
        'name': ['OidR'],
        'position': 9,
        'button': [],
        'cmd': ['sudo reboot'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'Shutdown oid': {
        'name': ['Oshut'],
        'position': 10,
        'button': [],
        'cmd': ['olm_shutdown_indihost'],
        'status': 0,
        'remote': True,
        'confirm': True
        },


    'Full shutdown': {
        'name': ['FShut'],
        'position': 11,
        'button': [],
        'cmd': ['olm_session_shutdown'],
        'status': 0,
        'remote': False,
        'confirm': True
        },

    'reinit EQ8 park West': {
        'name': ['ParkRst'],
        'position': 12,
        'button': [],
        'cmd': ['olm_in_eq8_reinitpark west'],
        'status': -1,
        'remote': True,
        'confirm': True
        },
    }

cmds2 = {
    'reinit EQ8 park West': {
        'name': ['reInit Park Info'],
        'position': 1,
        'button': [],
        'cmd': ['olm_in_eq8_reinitpark west'],
        'status': -1,
        'remote': True,
        'confirm': True
        },
    }
