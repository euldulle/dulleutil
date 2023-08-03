#!/usr/bin/python3
#
from __future__ import print_function
import time, sys, _thread, tty, termios
from time import sleep
import RPi.GPIO as GPIO
import curses
import signal
#from piobs_gpio_assignments import *
from gpio_filter_assignments import *

def clean_exit(signum, frame):
    global file
    curses.nocbreak(); 
    stdscr.keypad(0); 
    curses.echo()
    curses.endwin()
    # termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
    GPIO.output(o_dir_fw, GPIO.HIGH)
    GPIO.output(o_step_fw, GPIO.HIGH)
    GPIO.output(o_enable_fw, GPIO.HIGH)
    GPIO.cleanup()
    try:
        file.close()
    except:
        pass
    print ("Exiting properly\n");
    sys.exit()
#
#
# Creating getch call
#
def getch():   # define non-Windows version
    fd = sys.stdin.fileno()
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
    return ch
 
#
# Init No key press 
#
keycode = None

#
# Threaded kb lookup
# 
def keypress():
    global keycode
    keycode = ord(getch())
 

def gpio_dc_on(dir):
    if (dir==1):
        GPIO.output(O_focus_in, GPIO.LOW)
        GPIO.output(O_focus_out, GPIO.HIGH)
    else:
        GPIO.output(O_focus_in, GPIO.HIGH)
        GPIO.output(O_focus_out, GPIO.LOW)

def gpio_dc_off():
        GPIO.output(O_focus_in, GPIO.LOW)
        GPIO.output(O_focus_out, GPIO.LOW)
        
def do_move_dc():
    global step_scale, step_range, step_inc, delay_step, step_pos, backlash_param
    count=step_scale[step_range]

    if (step_inc==do_move_dc.lastdir):
        backlash=0
    else:
        backlash=1

    delay= 1.*((step_scale[step_range]+backlash_param*backlash)/step_scale[max_range])
    delay_disp= 1.*((step_scale[step_range])/step_scale[max_range])
    gpio_dc_on(step_inc)
    sleep(delay)

    if (step_inc==1):
        step_pos=(step_pos+delay_disp*scale_delay)
    else:
        step_pos=(step_pos-delay_disp*scale_delay)
        
    do_move_dc.lastdir=step_inc
    gpio_dc_off()


################################################
# 
################################################

  ####    #####    ##    #####    #####
 #          #     #  #   #    #     #
  ####      #    #    #  #    #     #
      #     #    ######  #####      #
 #    #     #    #    #  #   #      #
  ####      #    #    #  #    #     #

signal.signal(signal.SIGINT, clean_exit)
_thread.start_new_thread(keypress, ())


stdscr = curses.initscr()
try:
    stdscr.curs_set(False)
    curses.curs_set(False)
except:
    pass
curses.noecho()
s="    DC  FOCUS    "
stdscr.addstr(0,0,s,curses.A_REVERSE)
s="  POS(arb)  SPD "
stdscr.addstr(1,1,s,curses.A_BOLD)

#step_scale=[1,2,5,10,20,50,100,200,500,1000,2000,5000,10000.] 
step_scale=[100,200,500,1000,2000,5000,10000.] 
max_range=6
step_range=4
step_inc=1
step_pos=0
delay_step=0.01
scale_delay=100
backlash_param=200
do_move_dc.lastdir=step_inc

#
#
# GPIO pin assingnment come from pioobs_gpio_assignments.py
#
GPIO.setmode(GPIO.BCM)

#
#
# GPIO pin dir settings
#
GPIO.setup(O_focus_in, GPIO.OUT) 
GPIO.setup(O_focus_out, GPIO.OUT) 
sleep(0.1)
#
# GPIO pin init
#
GPIO.output(O_focus_out,GPIO.LOW)
GPIO.output(O_focus_out,GPIO.HIGH)
#
# saving term settings
#
fd = sys.stdin.fileno()
initial_settings = termios.tcgetattr(fd)

#
#
# 
gpio_dc_off()

while True:
    gpio_dc_off()

    if keycode==27:
        keycode=ord(getch())
        if keycode==91:
            keycode=ord(getch())
            if keycode==65:   # up
                step_range=min(max_range,step_range+1)
            elif keycode==66: # down
                step_range=max(0,step_range-1)
            elif keycode==67: # right
                step_inc=1;
                do_move_dc()
            elif keycode==68: # left
                step_inc=-1;
                do_move_dc()
    elif keycode==122:
        step_pos=0
    elif keycode==3:
        termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
        curses.nocbreak(); 
        stdscr.keypad(0); 
        curses.echo()
        curses.endwin()
        #GPIO.cleanup()
        sys.exit()
        break
    if keycode is not None:
        #print keycode
        keycode=None
        _thread.start_new_thread(keypress, ())
    s="\n %+6d  %5d\n\n\n"%(step_pos, step_scale[step_range])
    try:
        stdscr.addstr(2,1,s,curses.A_BOLD)
    except:
        print ("Erreur (fenetre trop petite ?)\r");
    stdscr.refresh()
    time.sleep(0.01)

GPIO.cleanup()
