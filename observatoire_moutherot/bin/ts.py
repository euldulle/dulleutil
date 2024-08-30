#!/usr/bin/python3
import time, sys, _thread, tty, termios
from time import sleep
import RPi.GPIO as GPIO
import curses
#from mx import DateTime
from gpio_filter_assignments import *

stdscr = curses.initscr()
try:
    stdscr.curs_set(False)
    curses.curs_set(False)
except:
    pass
curses.noecho()
s="    STEP TAK FOCUS    "
stdscr.addstr(0,0,s,curses.A_REVERSE)
s="  POS(um)  INC (um) "
stdscr.addstr(1,1,s,curses.A_BOLD)

step_scale=[1,2,5,10,20,50,100,200,500,1000,2000,5000,10000]
step_dir=-1
max_range=12
step_range=0
step_inc=1
old_dir=1
step_pos=0
ustep_count=0
steps_per_um=0.0104
usteps_per_step=32
delay_step=0.01/usteps_per_step
usteps_per_um=steps_per_um*usteps_per_step
backlash_param=float(5*usteps_per_step)
backlash_param=250
#
#
# GPIO pin assingnment
#
#o_step_c14=26
#o_dir_c14=19
#o_enable_c14=13

GPIO.setmode(GPIO.BCM)

#
#
# GPIO pin dir settings
#
GPIO.setup(o_step_c14, GPIO.OUT)
GPIO.setup(o_dir_c14, GPIO.OUT)
GPIO.setup(o_enable_c14, GPIO.OUT)
#
# GPIO pin init
#
GPIO.output(o_step_c14,GPIO.HIGH)
GPIO.output(o_step_c14,GPIO.LOW)
GPIO.output(o_dir_c14,GPIO.HIGH)
GPIO.output(o_dir_c14,GPIO.LOW)
GPIO.output(o_enable_c14,GPIO.HIGH)

#
#
# saving term settings
#
fd = sys.stdin.fileno()
initial_settings = termios.tcgetattr(fd)

#
#
# Creating getch call
#
try:
    from msvcrt import getch  # try to import Windows version
except ImportError:
    def getch():   # define non-Windows version
        fd = sys.stdin.fileno()
#        try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        return ch
#       finally:
#           termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
#       return ch

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

_thread.start_new_thread(keypress, ())

def do_move():
    global step_scale, step_range, step_inc, delay_step, step_pos, backlash_param, old_dir, ustep_count, step_dir

    GPIO.output(o_enable_c14,GPIO.HIGH)

    count=usteps_per_um*step_scale[step_range]
    if old_dir!=step_inc:
        count=count+backlash_param
    old_dir=step_inc
    if step_inc==1:
        GPIO.output(o_dir_c14, GPIO.LOW)
    else:
        GPIO.output(o_dir_c14, GPIO.HIGH)

    while count>0:
        count=count-1
        GPIO.output(o_step_c14, GPIO.HIGH)
        sleep(delay_step)
        GPIO.output(o_step_c14, GPIO.LOW)
        sleep(delay_step)
        ustep_count=ustep_count+step_inc
    step_pos=(step_pos+step_dir*step_inc*step_scale[step_range])
    GPIO.output(o_enable_c14,GPIO.HIGH)
    GPIO.output(o_enable_c14,GPIO.LOW)

pwr_stepper(ts_drv_addr, ON)
#
#
#
# n=DateTime.now()
while True:
    if keycode==27:
        keycode=ord(getch())
        if keycode==91:
            keycode=ord(getch())
            if keycode==65:   # up
                step_range=min(max_range,step_range+1)
            elif keycode==66: # down
                step_range=max(0,step_range-1)
            elif keycode==68: # right
                step_inc=1;
                do_move()
            elif keycode==67: # left
                step_inc=-1;
                do_move()
    elif keycode==122:
        step_pos=0
        ustep_count=0
    elif keycode==3:
        termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
        curses.nocbreak();
        stdscr.keypad(0);
        curses.echo()
        curses.endwin()
        GPIO.cleanup()
        pwr_stepper(ts_drv_addr, OFF)
        sys.exit()
        break

    if keycode is not None:
        #print keycode
        keycode=None
        _thread.start_new_thread(keypress, ())
    #s="\n %+6d  %7.1f\n\n    %s\n"%(step_pos*steps_per_um, steps_per_um*step_scale[step_range],n.strftime("%H:%M:%S"))
    s="\n %+6d  %7.1f\n\n  usteps : %d  %s\n"%(step_pos, step_scale[step_range], ustep_count, "ready")
    try:
        stdscr.addstr(2,1,s,curses.A_BOLD)
    except:
        #print ("%s Erreur (fenetre trop petite ?)\r"%(n.strftime("%H:%M:%S")));
        print ("%s Erreur (fenetre trop petite ?)\r"%("bin non"));
    stdscr.refresh()
#    n=DateTime.now()
    time.sleep(0.01)

pwr_stepper(ts_drv_addr, OFF)
