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

class SSHClient:
    def __init__(self, host, port, username, private_key_file):
        self.host = host
        self.port = port
        self.username = username
        self.private_key_file = private_key_file
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    def connect(self):
        try:
            # Load SSH private key
            private_key = paramiko.RSAKey.from_private_key_file(self.private_key_file)
            
            # Connect to SSH server using key-based authentication
            self.client.connect(self.host, self.port, self.username, pkey=private_key)
            print(f"Connected to {self.host}")
        except Exception as e:
            print(f"Connection failed: {e}")
            raise

    def send_command(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode('utf-8')

    def close(self):
        if self.client:
            self.client.close()
            print(f"Connection to {self.host} closed")


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
        'status': -1
        },

    'movecover': {
        'name': ['Close Cover','Open Cover'],
        'position': 2,
        'button': [],
        'cmd': ['closecov','opencov'],
        'status': 0,
        'states': ["OPENED", "CLOSED"],
        },

    'movebath': {
        'name': ['Close Bath','Open Bath'],
        'position': 3,
        'button': [],
        'cmd': ['closebat','openbat'],
        'status': 0,
        'statesname': ["OPENED", "CLOSED"],
        },
    }


def get_relay8_status():
    try:
        status=make_http_request(relay8_read).text.splitlines()
    except:
        print(relay8_read, " request failed")
        return
    filtered=[line for line in status if ': ' in line]
    fields=filtered[0].split()
    for i in range(1,8):
        match="Relay%d"%i
        relay=relays_8[match]
        if relay['position']>=0:
            if fields[i]!=relay['status']:
                relay['status']="OFF" if fields[i] == '0' else 'ON'
            relay['button'].config(fg='red' if relay['status'] == 'OFF' else 'green')

def get_relay16_status():
    with open ("/tmp/relay16", "w") as f:
        for i in range(4):
            try:
                f.write(make_http_request(relay16_read).text)
            except:
                print(relay16_read, " request failed")

    status16="cat /tmp/relay16 |sed 's/<p>R/<p> R/g;s/<p> R/\n<p> R/g;s@&nbsp@@g'|\
    grep 'Relay...:'|\
    sed 's@<center.*@@;s@<small>.*</small>@@;s@> ON/@>ON/@;s@>O@ >O@g;s@</font>@@;s@028@0.28@;s@href=@@;s@\"@@g'|\
    awk '{print $2 \" \" $5 \" \" $7}'"
    status16="cat /tmp/relay16 |sed 's/<p>R/<p>\ R/g;s/<p> R/\\n<p> R/g;s@&nbsp@@g'|grep 'Relay...:'|"
    status16+="sed 's@<center.*@@;s@<small>.*</small>@@;s@> ON/@>ON/@;s@>O@ >O@g;s@</font>@@;s@028@0.28@;s@href=@@;s@\"@@g;s@: @ @'|"
    status16+="awk '{print $2 \" \" $5 \" \" $7}'"

    # Execute the command
    process = subprocess.Popen(status16, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Wait for the process to complete and capture output
    stdout, stderr = process.communicate()

    # Check the return code
    return_code = process.returncode
    if return_code == 0:
        for line in stdout.splitlines():
            fields=line.split()
            if fields[0] in relays_16:
                relay=relays_16[fields[0]];
                if fields[1]!=relay['status']:
                    relay['status']=fields[1]
                    relay['button'].config(fg='red' if relay['status'] == 'OFF' else 'green')

                relay['url']=fields[2]
            
    else:
        print("Command '{command}' failed with return code {return_code}\nError: {stderr.strip()}")

def make_http_request(url):
    try:
        # Send GET request to the specified URL
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Process the response data (in this example, just print it)
            return response
        else:
            print(f"HTTP Request Failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., connection error, timeout)
        print(f"HTTP Request Error: {e}")

def invert_last_bit_in_url(url):
    # Find the last segment of the URL that contains the hexadecimal value
    match = re.search(r'/([0-9a-fA-F]{2})$', url)
    
    if match:
        # Extract the hexadecimal value from the URL
        hex_value = match.group(1)
        
        # Convert the hexadecimal value to an integer
        decimal_value = int(hex_value, 16)
        
        # Flip the least significant bit (LSB)
        inverted_value = decimal_value ^ 0x01
        
        # Convert the inverted value back to a hexadecimal string
        inverted_hex = format(inverted_value, '02x')  # Format as a 2-character hexadecimal string
        
        # Replace the original hexadecimal value with the inverted value in the URL
        modified_url = url[:match.start(1)] + inverted_hex + url[match.end(1):]
        
        return modified_url
    else:
        # If no match is found (e.g., no hexadecimal value in the URL), return the original URL
        return url

network="192.168.1"
r16ip=network+".28"
r16=r16ip+"/30"
relay16_read="http://"+r16+"/43"

r8ip=network+".23"
relay8_read="http://fmeyer:4so4xRg9@"+r8ip+"/relays.cgi"

buttons=[]
grid_frame16 = []
grid_frame8 = []



