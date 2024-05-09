#!/usr/bin/python
import os
import tkinter as tk
import requests
import subprocess
import re
import asyncio
from time import sleep
import paramiko
from  relay_rsc import *

# Function to quit the application
def quit_application():
    root.destroy()  # Close the main window and terminate the application

def read_status():
    get_relay8_status()
    get_relay16_status()
    get_cmd_status()
    root.after(5000, read_status)


# Define internal functions to be executed for each cell
def callback8( relais):
    request=relay8_read+"?relay=%d"%relaiss['addr']
    try:
        make_http_request(request)
    except:
        print("R8 command request failed: ",request)
    get_relay8_status()

def callback16(relais):
    try:
        make_http_request(relais['url'])
    except:
        print("R16 command request failed: ",relais['url'])
    url=invert_last_bit_in_url(relais['url'])
    #print(url)
    if relais['type']=='TEMP':
        sleep(.1)
        make_http_request(url)

    get_relay16_status()

def get_cmd_status():
    font='Helvetica'
    fontsize=10
    covstatus=ssh_client.send_command("gstatus").strip().split()

    cov=int(covstatus[0])
    other=int(covstatus[1])
    for com in cmds['movecover'],cmds['movebath']:
        com['status']=cov
        com['button'].config(fg='red' if com['status'] == 'CLOSED' else 'green',
                             text=com['name'][com['status']],
                             command=lambda relais=com, cmd=com['cmd'][com['status']]: 
                             remote_cmd(relais, cmd),
                             state=tk.DISABLED if other == 1 else tk.NORMAL,
                             font=(font, fontsize))
        cov=int(covstatus[1])
        other=int(covstatus[0])

def remote_cmd(relais, cmd):
    print("sending "+ cmd)
    ssh_client.send_command(cmd)
    print("sent "+ cmd)
    get_cmd_status()

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
            if rset==0:
                relay['button'] = tk.Button(frame, text=button_text, width=20, height=2,
                               fg='red' if relay['status']!=0 else 'green',
                               command=lambda cmd=relay['cmd'][relay['status']], 
                                            relais=relay: remote_cmd(relais, cmd),
                                            font=(font, fontsize))

            row=relay['position']+incpos
            #relay['button'].grid(row=row, column=0, padx=1, pady=1)
            relay['button'].grid(row=row, column=0)

            buttons.append(relay['button'])

# Example usage:
if __name__ == "__main__":
    #url = "https://jsonplaceholder.typicode.com/posts/1"  # Example URL (replace with your URL)
    #make_http_request(url)
    # Create the GUI
    # Start the GUI main loop
    # Create the GUI
    root = tk.Tk()
    root.title("Obs Moutherot control")

    # Frame to hold the grid of relay indicators for series 1
    grid_frame16 = tk.Frame(root)
    grid_frame16.pack(side=tk.LEFT)

    # Frame to hold the grid of commands
    grid_cmd = tk.Frame(root)
    #grid_frame8.pack(side=tk.RIGHT, padx=10, pady=10)
    grid_cmd.pack(side=tk.RIGHT)

    # Frame to hold the refresh button and grid
    top_frame = tk.Frame(root)
    top_frame.pack()

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

    create_grid(relays_16.items(),16)
    create_grid(relays_8.items(),8)
    create_grid(cmds.items(),0)

    # Quit button
    quit_button = tk.Button(grid_cmd, text="Quit", command=quit_application)
    quit_button.grid(row=8, column=0)

    # Initialize SSH client with SSH key authentication
    ssh_key_file = '/home/fmeyer/.ssh/obsm'
    ssh_client = SSHClient('oid', 22, 'fmeyer', ssh_key_file)
    read_status()
    root.mainloop()
