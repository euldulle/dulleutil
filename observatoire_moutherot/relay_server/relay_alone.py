#!/usr/bin/python
import os
import tkinter as tk
from tkinter import messagebox
import requests
import subprocess
import re
import asyncio
from time import sleep
import paramiko
import socket
from relay_rsc import *
from datetime import datetime  # Import datetime module for timestamp

class SSHClient:
    def __init__(self, host, port, username, private_key_file):
        self.host = host
        self.port = port
        self.username = username
        self.private_key_file = private_key_file
        self.client = paramiko.SSHClient()
        self.transport = self.client.get_transport()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    def connect(self):
        try:
            # Load SSH private key
            sock = socket.create_connection((self.host, self.port), timeout=1)
            private_key = paramiko.RSAKey.from_private_key_file(self.private_key_file)

            # Connect to SSH server using key-based authentication
            self.client.connect(self.host, self.port, self.username, pkey=private_key,sock=sock)
            self.transport=self.client.get_transport()
            print(f"Connected to {self.host}")

        except:
            add_log(f"ssh connect %s failed"%self.host)

    def send_command(self, command):
        if self.transport and self.transport.is_active():
            try:
                stdin, stdout, stderr = self.client.exec_command(command)
                return stdout.read().decode('utf-8')
            except:
                add_log("ssh send_cmd %s failed "%self.host)
                return "failed"

    def close(self):
        if self.client:
            self.client.close()
            add_log(f"Connection to {self.host} closed")


def confirm_action(action):
    # Display a confirmation dialog
    confirmed = messagebox.askyesno('Confirm', action)
    if confirmed:
        # User clicked 'Yes' to confirm the action
        return True
        # Add your action logic here (e.g., execute a function or command)
    else:
        # User clicked 'No' or closed the dialog
        return False

def update_time():
    current_time = datetime.now().strftime("%H:%M:%S")  # Format time as YYYY-MM-DD HH:MM:SS
    clock.config(text=current_time)  # Clear existing text
    root.after(1000, update_time)  # Update every 1000 ms (1 second)

def get_relay8_status():
    try:
        status=make_http_request(relay8_read).text.splitlines()
    except:
        add_log(" Relay8 request failed (%s)"%relay8_read)
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
        try:
            for i in range(4):
                f.write(make_http_request(relay16_read).text)
        except:
            add_log("Relay16 request failed (%s)"%relay16_read)
            return

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
        response = requests.get(url, timeout=(.5,.5))
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Process the response data (in this example, just print it)
            return response
        else:
            print(f"HTTP Request Failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., connection error, timeout)
        print(f"HTTP Request Error")

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
call_counter=0
# Function to quit the application
def quit_application():
    root.destroy()  # Close the main window and terminate the application

def read_status():
    global ssh_client, call_counter
    pollper=5           # poll every 5 seconds
    logfreq=60          # log every 60 seconds
    maxcount=logfreq/pollper

    call_counter = (call_counter+1) % maxcount
    if call_counter == 1:
        add_log("Mark")
    get_relay8_status()
    get_relay16_status()
    get_cmd_status()
    try:
        if not ssh_client.transport.is_active():
            ssh_client.connect()
    except:
        ssh_client.connect()

    root.after(1000*pollper, read_status)

# Define internal functions to be executed for each cell
def callback8( relais):
    request=relay8_read+"?relay=%d"%relais['addr']
    try:
        make_http_request(request)
    except:
        add_log("R8 command request failed: %s"%request)
    get_relay8_status()

def callback16(relais):
    try:
        make_http_request(relais['url'])
    except:
        add_log("R16 command request failed: %s"%relais['url'])
    url=invert_last_bit_in_url(relais['url'])
    #print(url)
    if relais['type']=='TEMP':
        sleep(.1)
        make_http_request(url)

    get_relay16_status()

def get_cmd_status():
    font='Helvetica'
    fontsize=10
    covstatus=ssh_client.send_command("gstatus")
    if covstatus:
        status=covstatus.strip().split()
        cov=int(status[0])
        bat=int(status[1])

        other=bat # tricky trickster
        for com in cmds['movecover'],cmds['movebath']:
            com['status']=cov
            com['button'].config(fg='red' if com['status'] == 'CLOSED' else 'green',
                                 text=com['name'][com['status']],
                                 command=lambda relais=com, cmd=com['cmd'][com['status']]:
                                 remote_cmd(relais, cmd),
                                 state=tk.DISABLED if other == 1 else tk.NORMAL,
                                 font=(font, fontsize))
            other=cov
            cov=bat

def remote_cmd(relais, cmd):
    if relais['confirm']:
        if not confirm_action(relais['name'][relais['status']]+' ?'):
            add_log(relais['name'][relais['status']]+" cancelled")
            return False
        print("confirmed")

    if relais['remote']:
        ssh_client.send_command(cmd)
        add_log("sent "+ cmd)
        get_cmd_status()
    else:
        syscom="/home/fmeyer/git/dulleutil/observatoire_moutherot/obslm.bash "+cmd
        process = subprocess.Popen(syscom, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        add_log("execd "+syscom)

def create_grid(items, rset):
    font='Helvetica'
    fontsize=10

    if rset==16:
        frame=grid_frame16
        incpos=1 # that's 1 for the title

    if rset==8:
        frame=grid_frame16
        incpos=18 # that's 2 for the titles, 16 for the relay16

    if rset==0:
        frame=grid_cmd
        incpos=1 # that's 1 for the title

    if rset==1:
        frame=grid_cmd2
        incpos=1 # that's 1 for the title

    for relayid,relay in items:
        if relay['position']>=0:
            button_text = relay['name'][0]

            # Create button and bind the corresponding function
            if rset==16:
                relay['button'] = tk.Button(frame, text=button_text, width=20, height=2,
                               fg='red' if relay['status']=="OFF" else 'green',
                               command=lambda relais=relay: callback16(relais),
                                            font=(font, fontsize))
            if rset==8:
                relay['button'] = tk.Button(frame, text=button_text, width=20, height=2,
                               fg='red' if relay['status']=="OFF" else 'green',
                               command=lambda relais=relay: callback8(relais),
                                            font=(font, fontsize))
            if rset==0 or rset==1:
                relay['button'] = tk.Button(frame, text=button_text, width=20, height=2,
                               fg='red' if relay['status']!=0 else 'green',
                               command=lambda cmd=relay['cmd'][relay['status']],
                                            relais=relay: remote_cmd(relais, cmd),
                                            font=(font, fontsize))

            row=relay['position']+incpos
            #relay['button'].grid(row=row, column=0, padx=1, pady=1)
            relay['button'].grid(row=row, column=0)

            buttons.append(relay['button'])

def add_log(message):
    global log_text

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get current timestamp in desired format
    formatted_message = f"{timestamp} {message}"  # Concatenate timestamp with message
    log_text.config(state=tk.NORMAL)  # Allow modifications to the Text widget
    log_text.insert(1.0, formatted_message + '\n')  # Insert message at the beginning (top) of the Text widget
    log_text.config(state=tk.DISABLED)  # Prevent further modifications to preserve read-only state

#url = "https://jsonplaceholder.typicode.com/posts/1"  # Example URL (replace with your URL)
#make_http_request(url)
# Create the GUI
# Start the GUI main loop
# Create the GUI
root = tk.Tk()
root.title("Obs Moutherot control")

# Create three frames for the first row (three vertical frames)
grid_frame16 = tk.Frame(root, width=200, height=100, bg="lightblue")
grid_cmd = tk.Frame(root, width=200, height=100, bg="lightgreen")
grid_cmd2 = tk.Frame(root, width=200, height=100, bg="lightcoral")

# Layout frames in the first row using grid
grid_frame16.grid(row=0, column=0, padx=10, pady=10)
grid_cmd.grid(row=0, column=1, padx=10, pady=10)
grid_cmd2.grid(row=0, column=2, padx=10, pady=10)

# Create a frame for the second row (single frame spanning full width)
bottom = tk.Frame(root, width=600, height=150, bg="lightyellow")

# Layout frame in the second row using grid
bottom.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# Configure row and column weights for resizing
root.grid_rowconfigure(0, weight=1)  # Allow first row to expand vertically
root.grid_rowconfigure(1, weight=1)  # Allow second row to expand vertically
root.grid_columnconfigure(0, weight=1)  # Allow column 0 to expand horizontally
root.grid_columnconfigure(1, weight=1)  # Allow column 1 to expand horizontally
root.grid_columnconfigure(2, weight=1)  # Allow column 2 to expand horizontally


# Create a scrolled Text widget for displaying error messages
log_text = scrolledtext.ScrolledText(bottom, width=120, height=10, wrap=tk.WORD)
log_text.pack(padx=10, pady=10)
log_text.config(state=tk.DISABLED)

# Refresh button spanning 2 columns
#refresh_button = tk.Button(top_frame, text="Refresh", command=read_status)
#refresh_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
# Frame to hold the grid of buttons
#grid_frame = tk.Frame(root)
#grid_frame.pack()

# Grids for the switch :
title_r16 = tk.Label(grid_frame16, text="Relay 16", font=("Helvetica", 16, "bold"))
title_r16.grid(row=0)

title_r8 = tk.Label(grid_frame16, text="Relay 8", font=("Helvetica", 16, "bold"))
title_r8.grid(row=17)

title_cmd = tk.Label(grid_cmd, text="Command Set #1", font=("Helvetica", 16, "bold"))
title_cmd.grid(row=1)

title_cmd2 = tk.Label(grid_cmd2, text="Command Set #2", font=("Helvetica", 16, "bold"))
title_cmd2.grid(row=0)

create_grid(relays_16.items(),16)
create_grid(relays_8.items(),8)
create_grid(cmds.items(),0)
create_grid(cmds2.items(),1)
clock = tk.Label(grid_cmd, height=1, width=10, font=("Helvetica", 18))
clock.config(anchor="center")
clock.grid(row=0, column=0)
#clock.pack(pady=20)

# Quit button
quit_button = tk.Button(grid_cmd, text="Quit", command=quit_application)
quit_button.grid(row=16, column=0)
# Initialize SSH client with SSH key authentication
ssh_key_file = '/home/fmeyer/.ssh/obsm'
ssh_client = SSHClient('oid', 22, 'fmeyer', ssh_key_file)
initial=0


update_time()
read_status()
root.mainloop()
