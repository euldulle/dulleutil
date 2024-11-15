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
    'Relay-01': {
        'name': ['Sfw'],
        'position': 6,
        'type': "SWITCH",
        'url': "",
        'button': [],
        'confirm': False,
        'status': "OFF"
        },

    'Relay-02': {
        'name': ['S14'],
        'url': "",
        'type': "SWITCH",
        'position': 7,
        'button': [],
        'confirm': False,
        'status': "OFF"
        },

    'Relay-03': {
        'name': ['Sts'],
        'url': "",
        'type': "SWITCH",
        'position': 8,
        'button': [],
        'confirm': False,
        'status': "OFF"
        },

    'Relay-04': {
        'name': ['pi3'],
        'url': "",
        'type': "SWITCH",
        'position': 9,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-05': {
        'name': ['LPi3'],
        'url': "",
        'type': "SWITCH",
        'position': 10,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-06': {
        'name': ['USB'],
        'url': "",
        'type': "SWITCH",
        'position': 0,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-07': {
        'name': ['Oid'],
        'url': "",
        'type': "SWITCH",
        'position': 2,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-08': {
        'name': ['DH'],
        'url': "",
        'type': "SWITCH",
        'position': 3,
        'button': [],
        'confirm': False,
        'status': "OFF"
        },

    'Relay-11': {
        'name': ['CCD'],
        'url': "",
        'type': "SWITCH",
        'position': 4,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-12': {
        'name': ['EQ8'],
        'url': "",
        'type': "SWITCH",
        'position': 1,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-13': {
        'name': ['Opn','Open Roof'],
        'url': "",
        'type': "TEMP",
        'position': 14,
        'confirm': True,
        'button': [],
        'status': "OFF"
        },

    'Relay-14': {
        'name': ['Clo','Close Roof'],
        'url': "",
        'type': "TEMP",
        'position': 12,
        'button': [],
        'confirm': True,
        'status': "OFF"
        },

    'Relay-15': {
        'name': ['Stp'],
        'url': "",
        'type': "TEMP",
        'position': 13,
        'confirm': False,
        'button': [],
        'status': "OFF"
        }

    }

relays_8 = {
    'Relay1': {
        'name': ['lgt','Light'],
        'position': 5,
        'button': [],
        'addr': 1,
        'status': "OFF",
        'confirm': False,
        'config': "NO" # normally open
        },

    'Relay2': {
        'name': ['pil','Alim Pilier'],
        'position': 0,
        'button': [],
        'addr': 2,
        'confirm': True,
        'status': "ON",
        'config': "NC" # normally closed
        },

    'Relay3': {
        'name': ['cam','Camera TIS'],
        'position': 3,
        'button': [],
        'addr': 3,
        'confirm': True,
        'status': "OFF",
        'config': "NO" # normally open
        },

    'Relay4': {
        'name': ['PrN','Prises Nord'],
        'position': 4,
        'button': [],
        'addr': 4,
        'status': "ON",
        'confirm': False,
        'config': "NC" # normally closed
        },

    'Relay5': {
        'name': ['PrS','Prises Sud'],
        'position': 2,
        'button': [],
        'addr': 5,
        'status': "ON",
        'confirm': False,
        'config': "NC" # normally closed
        },

    'Relay6': {
        'name': ['R16','Relais 16 ports'],
        'position': 1,
        'button': [],
        'addr': 6,
        'status': "ON",
        'confirm': True,
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
        'position': 3,
        'button': [],
        'cmd': ["olm_in_sync_eq8_time"],
        'status': -1,
        'remote': True,
        'confirm': False
        },

    'movecover': {
        'name': ['Cover1','Cover0'],
        'position': 0,
        'button': [],
        'cmd': ['closecov','opencov'],
        'status': 0,
        'states': ["OPENED", "CLOSED"],
        'remote': True,
        'confirm': False
        },

    'movebath': {
        'name': ['Bath1','Bath0'],
        'position': 1,
        'button': [],
        'cmd': ['closebat','openbat'],
        'status': 0,
        'statesname': ["OPENED", "CLOSED"],
        'remote': True,
        'confirm': False
        },

    'cycle qhy': {
        'name': ['QHYCyc'],
        'position': 8,
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
        'position': 2,
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
        'position': 4,
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
