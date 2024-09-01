#!/usr/bin/python3
import time, sys, _thread, tty, termios
from time import sleep
import RPi.GPIO as GPIO
import curses
import socket
from math import ceil
#from mx import DateTime
from gpio_filter_assignments import *

def errprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs,flush=True)

def init_listen_udp(port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', port))
    return udp_socket

def udp_update_pos():
    message, addr = udpsocket.recvfrom(32)  # Buffer size is 32 bytes
    final,large,small,status=message.decode().split()
    return float(final),float(large),float(small),int(status)

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
usteps_per_um=0.600
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

def get_usteps_from_dist(dist,rate):
    # dist is in mm
    # rate is in usteps per mm
    #
    # return value is in usteps
    return int(ceil(dist)*rate)

def goto(target, initial, usteps):
    errprint("0 to: %f, from: %f est: %d\n"%(target, initial, usteps))
    initial,large,small,status=udp_update_pos()
    errprint("1 to: %f, from: %f est: %d\n"%(target, initial, usteps))
    errprint("1st move usteps %d\n"%usteps)
    do_move(usteps)
    for i in range(5):
        new,large,small,status=udp_update_pos()
    errprint("After 1st move : target %.3f final %.3f delta %.3f \n"%(target,new,new-target))

    # get an update of the ratio um/ustep
    # based on last move :
    rate=abs(new-current)/usteps
    nextmove=get_usteps_from_dist(new-current,rate)
    newtarget=(target-new)

def do_move(usteps):
    global step_scale, step_range, delay_step, step_pos, old_dir, ustep_count, step_dir, udpsocket,logmsg
    if usteps==0:
        return 
    GPIO.output(o_enable_c14,GPIO.HIGH)
   
    if (usteps>0):
        # outwards increase backfocus
        GPIO.output(o_dir_c14, GPIO.HIGH)
    else:
        # inwards decrease backfocus
        GPIO.output(o_dir_c14, GPIO.LOW)
        usteps=-usteps

    while (usteps>0):
        usteps-=1
        GPIO.output(o_step_c14, GPIO.HIGH)
        sleep(delay_step)
        GPIO.output(o_step_c14, GPIO.LOW)
        sleep(delay_step)
    #logmsg="C%d"%count

    GPIO.output(o_enable_c14,GPIO.HIGH)
    GPIO.output(o_enable_c14,GPIO.LOW)

global udpsocket, logmsg, OUTWARDS, INWARDS
OUTWARDS=1
INWARDS=-1

udpsocket=init_listen_udp(2345)
final=0
pwr_stepper(ts_drv_addr, ON)
logmsg="ready"
#
#
#
# n=DateTime.now()
target=0
while True:
    delta_dist=float(step_scale[step_range]) # requested delta_dist in um
    delta_usteps=get_usteps_from_dist(delta_dist,usteps_per_um) # corresponding nr of usteps
    current,large,small,status=udp_update_pos()
    if keycode==27:
        keycode=ord(getch())
        if keycode==91:
            keycode=ord(getch())
            if keycode==65:   # up
                step_range=min(max_range,step_range+1)
            elif keycode==66: # down
                step_range=max(0,step_range-1)
            elif keycode==68: # left inwards
                target=current-delta_dist/1000
                goto(target,current,-delta_usteps)
            elif keycode==67: # left
                target=current+delta_dist/1000 # target in mm
                goto(target,current,+delta_usteps)
                #logmsg="T%.3f"%target
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
    #s="\n %+6d  %7.1f\n\n  usteps : %d  %s\n"%(step_pos, step_scale[step_range], ustep_count, "ready")
    s="\n %+7.3f  %7.1f\n\n  udp : %s  %s\n"%(current, step_scale[step_range], final, logmsg)
    try:
        stdscr.addstr(2,1,s,curses.A_BOLD)
    except:
        #print ("%s Erreur (fenetre trop petite ?)\r"%(n.strftime("%H:%M:%S")));
        print ("%s Erreur (fenetre trop petite ?)\r"%("bin non"));
    stdscr.refresh()
#    n=DateTime.now()
    sys.stderr.flush()
    time.sleep(0.01)

pwr_stepper(ts_drv_addr, OFF)
