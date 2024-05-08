#!/usr/bin/python
import os
import tkinter as tk
import requests
import subprocess
network="192.168.1"
r16ip=network+".28"
r16=r16ip+"/30"
relay16_read="http://"+r16+"/43"
relay8_read="http://fmeyer:4so4xRg9@${OLM_R8IP}${OLM_R8PORT}/relays.cgi"
buttons=[]
indicators=[]
grid_frame16 = []
grid_frame8 = []

# Function to toggle the switch status (for demonstration)
def toggle_switch_status():
    global is_switch_on
    is_switch_on = not is_switch_on
    update_indicators()

# Function to update the indicator colors based on switch status
def update_indicators():
    for button, indicator in zip(buttons, indicators):
        if is_switch_on:
            indicator.config(bg='green')  # Set indicator color to green if switch is on
        else:
            indicator.config(bg='red')  # Set indicator color to red if switch is off

# Initialize switch status (for demonstration)
is_switch_on = False

relays_16 = {
    'Relay-12': {
        'name': 'USB HUB',
        'position': 0,
        'state': 0
        },

    'Relay-13': {
        'name': 'EQ8',
        'position': 1,
        'state': 0
        },

    'Relay-10': {
        'name': 'Oid',
        'position': 2,
        'state': 0
        },

    'Relay-09': {
        'name': 'Dew Heater',
        'position': 3,
        'state': 0
        },

    'Relay-11': {
        'name': 'CCD',
        'position': 4,
        'state': 0
        },

    'Relay-01': {
        'name': 'FW Stepper',
        'position': 5,
        'state': 0
        },

    'Relay-02': {
        'name': 'C14 Stepper',
        'position': 6,
        'state': 0
        },

    'Relay-03': {
        'name': 'TS Stepper',
        'position': 7,
        'state': 0
        }
    }

relays_8 = {
    'Relay1': {
        'name': 'light',
        'position': 0,
        'state': 0
        },

    'Relay2': {
        'name': 'pilier',
        'position': 1,
        'state': 0
        },

    'Relay3': {
        'name': 'camera',
        'position': 2,
        'state': 0
        },

    'Relay4': {
        'name': 'Prises N',
        'position': 3,
        'state': 0
        },

    'Relay5': {
        'name': 'Prises S (Toit)',
        'position': 4,
        'state': 0
        },

    'Relay6': {
        'name': 'Relay16',
        'position': 5,
        'state': 0
        },

    'Relay7': {
        'name': 'CCD',
        'position': -1,
        'state': 0
        },

    'Relay8': {
        'name': 'CCD',
        'position': -1,
        'state': 0
        }
    }


# Function to quit the application
def quit_application():
    root.destroy()  # Close the main window and terminate the application

def get_relay8_status():
    with open ("/tmp/relay8", "w") as f:
        make_http_request(relay16_read).text

    # Destroy all existing buttons
    for button in grid_frame8.winfo_children():
        button.destroy()

    # Recreate the grid of buttons
    create_grid(relays_18.items(),16)



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
            print(fields)
            if fields[0] in relays_16:
                relays_16[fields[0]]['state']=fields[1]
            
    else:
        print("Command '{command}' failed with return code {return_code}\nError: {stderr.strip()}")

    # Destroy all existing buttons
    for button in grid_frame16.winfo_children():
        button.destroy()

    # Recreate the grid of buttons
    create_grid(relays_16.items(),16)


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




# Define internal functions to be executed for each cell
def callback8(relayid, relais):
    print("Function r8 was called!",relayid, relais['name'])

def callback16(relayid, relais):
    print("Function r16 was called!",relayid, relais['name'])
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
                button = tk.Button(frame, text=button_text, width=20, height=2,
                               command=lambda rid=relayid, relais=relay: callback16(rid,relais))
            else:
                button = tk.Button(frame, text=button_text, width=20, height=2,
                               command=lambda rid=relayid, relais=relay: callback8(rid,relais))
            row=relay['position']
            button.grid(row=row, column=0, padx=5, pady=5)

            # Indicator labels for series 1
            if relay['state']=="OFF":
                indicator = tk.Label(frame, text='OFF', fg='red', width=5)
            else:
                indicator = tk.Label(frame, text='ON', fg='green', width=5)
            indicator.grid(row=row, column=1, sticky='nw')

            buttons.append(button)
            indicators.append(indicator)

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
    refresh_button = tk.Button(top_frame, text="Refresh", command=get_relay16_status)
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


    root.mainloop()
