#!/usr/bin/python3
import time, sys, _thread, tty, termios
from time import sleep
import RPi.GPIO as GPIO
import curses
import socket
import threading

from math import ceil
#from mx import DateTime
from gpio_filter_assignments import *

keycode=None
shared_final = None
udpsocket=None
logmsg=None
OUTWARDS=1
INWARDS=-1
backlash=None
lock = threading.Lock()
stdscr=None
logfile=None
minFocus=0.1
maxFocus=9.1
centerFocus=(maxFocus+minFocus)/2

def sign(x):
    return (x > 0) - (x < 0)

def errprint(*args, **kwargs):
    global logfile
    print(*args, file=logfile, **kwargs,flush=True)

def init_listen_udp(port):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', port))
    return udp_socket

def udp_update_pos(event):
    global shared_final
    udpsocket=init_listen_udp(2345)
    while not event.is_set():
        message, addr = udpsocket.recvfrom(32)  # Buffer size is 32 bytes
        final,large,small,status=message.decode().split()

        with lock:
            shared_final=float(final)

#
# Threaded kb lookup
#
def keypress(event):
    global keycode
    while not event.is_set():
        keycode = ord(getch())
        sleep(.01)


def get_usteps_from_dist(dist,rate):
    # dist is in mm
    # rate is in usteps per um
    #
    # return value is in usteps
    return abs(int(ceil(dist)*rate))

def goto(target): # direction = INWARDS (-1) or OUTWARDS (+1)
    global backlash, shared_final, usteps_per_um, accuracy, maxFocus, minFocus
    if target > maxFocus:
        errprint("Goto : max outfocus reached")
        target=maxFocus
    if target < minFocus:
        errprint("Goto : min backfocus reached")
        target=minFocus
    maxmove=60
    count=0
    with lock:
        current=shared_final
    delta_dist=target-current
    direction=sign(delta_dist)
    usteps=get_usteps_from_dist(delta_dist,usteps_per_um) # corresponding nr of usteps

    try:
        usteps=backlash*(direction!=goto.direction)+usteps
    except:
        goto.direction=direction

    errprint("Goto : target %.3f current %.3f acc %.3f"%(target,shared_final,accuracy))
    while(abs(target-current)>accuracy and count<maxmove):
        count+=1
        errprint("DoMove : %d steps dir %d (target %.3f current %.3f)"%(usteps,direction,target,current))
        usteps=backlash*(direction!=goto.direction)+max(4,get_usteps_from_dist(1000*(current-target),usteps_per_um))
        do_move(usteps,direction)
        goto.direction=direction
        sleep(.15)
        with lock:
            current=shared_final
        direction=sign(target-current)
        usteps=backlash*(direction!=goto.direction)+max(4,get_usteps_from_dist(1000*(current-target),usteps_per_um))
    with lock:
        final=shared_final
    if(count>=maxmove):
        errprint("Max reached Goto : target %.3f final %.3f delta %.3f \n"%(target,final,final-target))
    else:
        errprint("Goto OK: target %.3f final %.3f delta %.3f \n"%(target,final,final-target))

def do_move(usteps,direction):
    global step_scale, step_range, delay_step1, delay_step2, step_pos, old_dir, ustep_count, step_dir, udpsocket,logmsg
    if usteps==0:
        return
    GPIO.output(o_enable_c14,GPIO.HIGH)

    if (direction==OUTWARDS):
        # outwards increase backfocus
        GPIO.output(o_dir_c14, GPIO.HIGH)
    else:
        # inwards decrease backfocus
        GPIO.output(o_dir_c14, GPIO.LOW)

    while (usteps>0):
        usteps-=1
        GPIO.output(o_step_c14, GPIO.HIGH)
        sleep(delay_step1)
        GPIO.output(o_step_c14, GPIO.LOW)
        sleep(delay_step2)

    GPIO.output(o_enable_c14,GPIO.HIGH)
    GPIO.output(o_enable_c14,GPIO.LOW)

def process_data(event):
    global shared_final, keycode, stdscr
    global backlash, usteps_per_um, delay_step1, delay_step2,accuracy
    backlash=150 # unit is ustep
    fdratio=8
    maxdistorsion=1./8. # min target lambda/8
    band=0.0006 # observing wavelength in mm
    accuracy = 8*fdratio*fdratio*band*maxdistorsion # unit is mm
    #accuracy = 0.005
    #udpsocket=init_listen_udp(2345)
    logmsg="ready"
    #stdscr = curses.initscr()
    try:
        stdscr.curs_set(False)
        curses.curs_set(False)
    except:
        pass
    curses.noecho()
    s="    STEP TAK FOCUS    "
    stdscr.addstr(0,0,s,curses.A_REVERSE)
    s="  POS(mm) (acc um)  INC (um) "
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
    delay_step1=0.05/usteps_per_step
    delay_step2=0.05/usteps_per_step
    usteps_per_um=0.400
    #
    #
    # GPIO pin assingnment
    #
    #o_step_c14=26
    #o_dir_c14=19
    #o_enable_c14=13


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
    # Init No key press
    #
    keycode = None

    while not event.is_set():
        delta_dist=float(step_scale[step_range]) # requested delta_dist in um
        # current,large,small,status=udp_update_pos()
        with lock:
            current=shared_final
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
                    goto(target)
                elif keycode==67: # left
                    target=current+delta_dist/1000 # target in mm
                    goto(target)
                    #logmsg="T%.3f"%target
        elif keycode==122: # z : goto middle of the focusing range
            goto(centerFocus)
        elif keycode==3 or keycode == 113 or keycode == 81: # ctrl-c or q or Q
            #pwr_stepper(ts_drv_addr, OFF)
            event.set() # telling everybody to vacate
            sys.exit()

            break

#        if keycode is not None:
            #print keycode
#            keycode=None
            #_thread.start_new_thread(keypress, ())
        if shared_final is not None:
            s="\n %+7.3f (%3d)  %7.1f\n\n  udp : %s\n"%(current, accuracy*1000, step_scale[step_range], logmsg)

        try:
            stdscr.addstr(2,1,s,curses.A_BOLD)
        except:
            #print ("%s Erreur (fenetre trop petite ?)\r"%(n.strftime("%H:%M:%S")));
            print ("%s Erreur (fenetre trop petite ?)\r"%("bin non"));
        stdscr.refresh()
    #    n=DateTime.now()
        sys.stderr.flush()
        time.sleep(0.01)

# Main function
if __name__ == "__main__":
    try:
        logfile=open(sys.argv[1],"w")
    except:
        logfile=open("/dev/null","w")
    #
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

    #pwr_stepper(ts_drv_addr, ON)
#
#
#

#
    #
    # saving term settings
    #
    fd = sys.stdin.fileno()
    initial_settings = termios.tcgetattr(fd)
    stdscr = curses.initscr()
    GPIO.setmode(GPIO.BCM)


    # Start the UDP listener thread
    event=threading.Event()
    listener_thread = threading.Thread(target=udp_update_pos,args=(event,))
    listener_thread.daemon = True
    listener_thread.start()

    keypress_thread = threading.Thread(target=keypress,args=(event,))
    keypress_thread.daemon = True
    keypress_thread.start()

    # Start the data processing thread
    processor_thread = threading.Thread(target=process_data,args=(event,))
    processor_thread.daemon = True
    processor_thread.start()

#    _thread.start_new_thread(keypress, ())

    # Keep the main thread alive
    while not event.is_set():
        time.sleep(1)

    termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
    curses.nocbreak();
    stdscr.keypad(0);
    curses.echo()
    curses.endwin()
    GPIO.cleanup()

    #pwr_stepper(ts_drv_addr, OFF)
