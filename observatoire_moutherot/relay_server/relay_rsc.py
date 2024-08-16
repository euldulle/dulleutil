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
        'name': ['USB HUB'],
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
        'name': ['Dew Heater'],
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
        'name': ['FW Stepper'],
        'position': 5,
        'type': "SWITCH",
        'url': "",
        'button': [],
        'status': "OFF"
        },

    'Relay-02': {
        'name': ['C14 Stepper'],
        'url': "",
        'type': "SWITCH",
        'position': 6,
        'button': [],
        'status': "OFF"
        },

    'Relay-03': {
        'name': ['TS Stepper'],
        'url': "",
        'type': "SWITCH",
        'position': 7,
        'button': [],
        'status': "OFF"
        },

    'Relay-14': {
        'name': ['Close Roof'],
        'url': "",
        'type': "TEMP",
        'position': 8,
        'button': [],
        'status': "OFF"
        },

    'Relay-15': {
        'name': ['Stop Roof'],
        'url': "",
        'type': "TEMP",
        'position': 9,
        'button': [],
        'status': "OFF"
        },

    'Relay-16': {
        'name': ['Open Roof'],
        'url': "",
        'type': "TEMP",
        'position': 10,
        'button': [],
        'status': "OFF"
        }
    }

relays_8 = {
    'Relay1': {
        'name': ['light'],
        'position': 0,
        'button': [],
        'addr': 1,
        'status': "OFF"
        },

    'Relay2': {
        'name': ['pilier'],
        'position': 1,
        'button': [],
        'addr': 2,
        'status': "OFF"
        },

    'Relay3': {
        'name': ['camera'],
        'position': 2,
        'button': [],
        'addr': 3,
        'status': "OFF"
        },

    'Relay4': {
        'name': ['Prises N'],
        'position': 3,
        'button': [],
        'addr': 4,
        'status': "OFF"
        },

    'Relay5': {
        'name': ['Prises S (Toit)'],
        'position': 4,
        'button': [],
        'addr': 5,
        'status': "OFF"
        },

    'Relay6': {
        'name': ['Relay16'],
        'position': 5,
        'button': [],
        'addr': 6,
        'status': "OFF"
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
        'name': ['Sync EQ8'],
        'position': 1,
        'button': [],
        'cmd': ["olm_in_sync_eq8_time"],
        'status': -1,
        'remote': True,
        'confirm': False
        },

    'movecover': {
        'name': ['Close Cover','Open Cover'],
        'position': 2,
        'button': [],
        'cmd': ['closecov','opencov'],
        'status': 0,
        'states': ["OPENED", "CLOSED"],
        'remote': True,
        'confirm': False
        },

    'movebath': {
        'name': ['Close Bath','Open Bath'],
        'position': 3,
        'button': [],
        'cmd': ['closebat','openbat'],
        'status': 0,
        'statesname': ["OPENED", "CLOSED"],
        'remote': True,
        'confirm': False
        },

    'cycle qhy': {
        'name': ['Cycle QHY'],
        'position': 4,
        'button': [],
        'cmd': ['olm_in_cycle qhy'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle eq8': {
        'name': ['Cycle EQ8'],
        'position': 5,
        'button': [],
        'cmd': ['olm_in_cycle eq8'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle ccd': {
        'name': ['Cycle CCD'],
        'position': 6,
        'button': [],
        'cmd': ['olm_in_cycle p1'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle fw': {
        'name': ['Cycle fw'],
        'position': 7,
        'button': [],
        'cmd': ['olm_in_cycle fw'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'cycle indi': {
        'name': ['Cycle indi'],
        'position': 8,
        'button': [],
        'cmd': ['olm_in_cycle indiserver'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'Reboot oid': {
        'name': ['Reboot oid'],
        'position': 9,
        'button': [],
        'cmd': ['sudo reboot'],
        'status': 0,
        'remote': True,
        'confirm': True
        },

    'Shutdown oid': {
        'name': ['Shutdown oid'],
        'position': 9,
        'button': [],
        'cmd': ['olm_shutdown_indihost'],
        'status': 0,
        'remote': True,
        'confirm': True
        },


    'Full shutdown': {
        'name': ['Full Shutdown'],
        'position': 10,
        'button': [],
        'cmd': ['olm_session_shutdown'],
        'status': 0,
        'remote': False,
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
