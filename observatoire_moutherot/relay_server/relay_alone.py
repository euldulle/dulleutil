#!/usr/bin/python
import os
import tkinter as tk
import requests
import subprocess
import re
import asyncio
from time import sleep

network="192.168.1"
r16ip=network+".28"
r16=r16ip+"/30"
relay16_read="http://"+r16+"/43"

r8ip=network+".23"
relay8_read="http://fmeyer:4so4xRg9@"+r8ip+"/relays.cgi"

buttons=[]
grid_frame16 = []
grid_frame8 = []

relays_16 = {
    'Relay-12': {
        'name': 'USB HUB',
        'url': "",
        'type': "SWITCH",
        'position': 0,
        'button': [],
        'state': "OFF"
        },

    'Relay-13': {
        'name': 'EQ8',
        'url': "",
        'type': "SWITCH",
        'position': 1,
        'button': [],
        'state': "OFF"
        },

    'Relay-10': {
        'name': 'Oid',
        'url': "",
        'type': "SWITCH",
        'position': 2,
        'button': [],
        'state': "OFF"
        },

    'Relay-09': {
        'name': 'Dew Heater',
        'url': "",
        'type': "SWITCH",
        'position': 3,
        'button': [],
        'state': "OFF"
        },

    'Relay-11': {
        'name': 'CCD',
        'url': "",
        'type': "SWITCH",
        'position': 4,
        'button': [],
        'state': "OFF"
        },

    'Relay-01': {
        'name': 'FW Stepper',
        'position': 5,
        'type': "SWITCH",
        'url': "",
        'button': [],
        'state': "OFF"
        },

    'Relay-02': {
        'name': 'C14 Stepper',
        'url': "",
        'type': "SWITCH",
        'position': 6,
        'button': [],
        'state': "OFF"
        },

    'Relay-03': {
        'name': 'TS Stepper',
        'url': "",
        'type': "SWITCH",
        'position': 7,
        'button': [],
        'state': "OFF"
        },

    'Relay-14': {
        'name': 'Close Roof',
        'url': "",
        'type': "TEMP",
        'position': 8,
        'button': [],
        'state': "OFF"
        },

    'Relay-15': {
        'name': 'Stop Roof',
        'url': "",
        'type': "TEMP",
        'position': 9,
        'button': [],
        'state': "OFF"
        },

    'Relay-16': {
        'name': 'Open Roof',
        'url': "",
        'type': "TEMP",
        'position': 10,
        'button': [],
        'state': "OFF"
        }
    }

relays_8 = {
    'Relay1': {
        'name': 'light',
        'position': 0,
        'button': [],
        'addr': 1,
        'state': "OFF"
        },

    'Relay2': {
        'name': 'pilier',
        'position': 1,
        'button': [],
        'addr': 2,
        'state': "OFF"
        },

    'Relay3': {
        'name': 'camera',
        'position': 2,
        'button': [],
        'addr': 2,
        'state': "OFF"
        },

    'Relay4': {
        'name': 'Prises N',
        'position': 3,
        'button': [],
        'addr': 2,
        'state': "OFF"
        },

    'Relay5': {
        'name': 'Prises S (Toit)',
        'position': 4,
        'button': [],
        'addr': 2,
        'state': "OFF"
        },

    'Relay6': {
        'name': 'Relay16',
        'position': 5,
        'button': [],
        'addr': 2,
        'state': "OFF"
        },

    'Relay7': {
        'name': 'CCD',
        'position': -1,
        'button': [],
        'addr': 2,
        'state': "OFF"
        },

    'Relay8': {
        'name': 'CCD',
        'position': -1,
        'button': [],
        'addr': 2,
        'state': "OFF"
        }
    }


# Function to quit the application
def quit_application():
    root.destroy()  # Close the main window and terminate the application

def read_status():
    get_relay8_status()
    get_relay16_status()
    root.after(5000, read_status)

def get_relay8_status():
    #with open ("/tmp/relay8", "w") as f:
    status=make_http_request(relay8_read).text.splitlines()
    filtered=[line for line in status if ': ' in line]
    print(filtered[0])


def get_relay16_status():
    with open ("/tmp/relay16", "w") as f:
        for i in range(4):
            f.write(make_http_request(relay16_read).text)

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
                if fields[1]!=relay['state']:
                    relay['state']=fields[1]
                    #relay['indicator'].config(text=relay['state'], fg='red' if relay['state'] == 'OFF' else 'green')
                    relay['button'].config(fg='red' if relay['state'] == 'OFF' else 'green')

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


# Define internal functions to be executed for each cell
def callback8(relayid, relais):
    print("Function r8 was called!",relayid, relais['name'])
    get_relay16_status()

def callback16(relayid, relais):
    #print("Function r16 was called!",relayid, relais['name'])
    #print(relays_16[relayid]['url'])
    make_http_request(relays_16[relayid]['url'])
    url=invert_last_bit_in_url(relays_16[relayid]['url'])
    #print(url)
    if relays_16[relayid]['type']=='TEMP':
        sleep(.1)
        make_http_request(url)

    get_relay16_status()

def create_grid(items, rset):
    if rset==16:
        frame=grid_frame16
    else:
        frame=grid_frame8

    for relayid,relay in items:
        if relay['position']>=0:
            button_text = relay['name']

            # Create button and bind the corresponding function
            if rset==16:
                relay['button'] = tk.Button(frame, text=button_text, width=20, height=2, 
                               fg='red' if relay['state']=="OFF" else 'green',
                               command=lambda rid=relayid, relais=relay: callback16(rid,relais),
                                            font=('Helvetica', 12 ))
            else:
                relay['button'] = tk.Button(frame, text=button_text, width=20, height=2,
                               command=lambda rid=relayid, relais=relay: callback8(rid,relais))
            row=relay['position']
            relay['button'].grid(row=row, column=0, padx=5, pady=5)

            buttons.append(relay['button'])

# Example usage:
if __name__ == "__main__":
    #url = "https://jsonplaceholder.typicode.com/posts/1"  # Example URL (replace with your URL)
    #make_http_request(url)
    # Create the GUI
    # Start the GUI main loop
    # Create the GUI
    root = tk.Tk()
    root.title("Clickable Grid")

    # Frame to hold the grid of relay indicators for series 1
    grid_frame16 = tk.Frame(root)
    grid_frame16.pack(side=tk.LEFT, padx=10, pady=10)

    # Frame to hold the grid of relay indicators for series 2
    grid_frame8 = tk.Frame(root)
    grid_frame8.pack(side=tk.RIGHT, padx=10, pady=10)

    # Frame to hold the refresh button and grid
    top_frame = tk.Frame(root)
    top_frame.pack()

    # Refresh button spanning 2 columns
    refresh_button = tk.Button(top_frame, text="Refresh", command=read_status)
    refresh_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    # Frame to hold the grid of buttons
    #grid_frame = tk.Frame(root)
    #grid_frame.pack()

    # Initial creation of the grid
    create_grid(relays_16.items(),16)
    create_grid(relays_8.items(),8)
    # Quit button
    quit_button = tk.Button(root, text="Quit", command=quit_application)
    quit_button.pack(side=tk.BOTTOM, padx=10, pady=10)
    read_status()

    root.mainloop()
