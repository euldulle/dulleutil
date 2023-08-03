#!/usr/bin/python3
#
from __future__ import print_function
import time, sys, _thread, tty, termios
from time import sleep
import RPi.GPIO as GPIO
import curses
import signal
import os
import urllib
import urllib.request


sys.path.insert(0, '/home/fmeyer/relay_server/web/page')
sys.path.insert(0, '/home/fmeyer/bin')
from gpio_filter_assignments import *
statusword=""
#
def stepper_driver_on(onoff):
    pass
    # FIXME
    # http://localhost:8028/page/relays.py?switch=http://192.168.0.28/30/01

def update_statefile(status):
    with open(olm_fw_statefile,"w") as f:
        print ("%d %s %s"%(filter_index,olm_fw_filters[filter_index],status),file=f)

def reset_index():
    while not check_reed():
        status_line(" Reed/motor not ready");
        update_statefile("INDEX_SEARCH")
        sleep(2)

def pwr_stepper(onoff):
    if onoff=="ON":
        urllib.request.urlretrieve("http://192.168.0.28/30/01")

    if onoff=="OFF":
        urllib.request.urlretrieve("http://192.168.0.28/30/00")

def clean_exit(signum, frame):
    global filter_index

    if filter_index==None or filter_index==0:
        filter_index=initindex

    update_statefile("NOT_RUNNING")
    pwr_stepper("OFF")

    if interactive:
        curses.nocbreak();
        stdscr.keypad(0);
        curses.echo()
        curses.endwin()
    # termios.tcsetattr(fd, termios.TCSADRAIN, initial_settings)
    GPIO.output(o_dir_fw, GPIO.HIGH)
    GPIO.output(o_step_fw, GPIO.HIGH)
    GPIO.output(o_enable_fw, GPIO.HIGH)
    GPIO.cleanup()
    os.close(fifofile)

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

def check_reed():
    global fail_count, statusword
#
# check if reed sensor is effective (and though if motor spins)
#
    fail_count=0
    do_move(reed_sensor_off)
    do_move(reed_sensor_on)
    do_move(reed_sensor_off)

    if fail_count>0:
        statusword="ERRSTEP"
        return(False)
    else:
        return(True)

def next():
    global filter_index, out_steps, align_steps,reed_sensor_off, reed_sensor_on, step_pos
    do_step(out_steps)
    do_move(reed_sensor_off)
    if step_pos > 400 and step_pos < 600:
        filter_index=0
        do_step(out_steps)
        do_move(reed_sensor_on)
        do_step(out_steps)
        do_move(reed_sensor_off)
        do_step(align_steps-40)
    else:
        do_step(align_steps)
    filter_index=1+(filter_index)%5

def seek_index(target):
    global filter_index, fail_count
    if target>0:
        while filter_index!=target and fail_count==0:
            status_line("filter_index %d target %d"%(filter_index, target))
            next()

def status_line(message=""):
    if interactive:
        s="@ Filter_index %.1d  @\n @ Step_pos %.5d@\n @ %s @\n @ Reed : %.1d @\n @ %s @\n"%(filter_index, step_pos, olm_fw_filters[filter_index], reed_state , message)
        stdscr.addstr(3,1,s,curses.color_pair(filter_index))
        stdscr.refresh()

def do_step(nb_step=1):
    global step_pos, delay_step, delay_steplow, reed_state

    GPIO.output(o_enable_fw, GPIO.LOW)
    for i in range (0,nb_step):
        # on incremente et on envoie un pas
        #
        step_pos=step_pos+1
        # print ("step %d/reed %d\r"%(step_pos,reed_state))

        GPIO.output(o_step_fw, GPIO.HIGH)
        # le delay_step est a ajuster en fonction du moteur
        sleep(delay_step)
        GPIO.output(o_step_fw, GPIO.LOW)
        sleep(delay_steplow)
    GPIO.output(o_enable_fw, GPIO.HIGH)


def do_move(wait_for):
    global reed_state, step_inc, delay_step, delay_steplow, step_pos, backlash_param, old_dir, stdscr, s, fail_count, LIMIT

    #
    # step_inc est le sens de rotation
    # la transmission est telle qu'il n'y a
    # qu'un sens qui fonctionne donc c'est plus simple
    # step_inc vaut toujours 1
    #
    if step_inc==1:
        GPIO.output(o_dir_fw, GPIO.LOW)
    else:
        GPIO.output(o_dir_fw, GPIO.HIGH)

    stop=False
    step_pos=0
    #
    # step_pos est le nombre de pas envoyes ; s'il depasse LIMIT
    # avant qu'on ait trouve ce qu'on cherche, on jette l'eponge
    #
    while not stop and step_pos < LIMIT:
        do_step(usteps_per_step)
        #do_step(1)
        status_line()
        #
        # si l'etat du reed sensor est ce qu'on attend,
        #
        reed_state=GPIO.input(o_sensor_fw)
        counter=0
        while reed_state==wait_for and counter <3:
            #
            # alors on envoie un pas de plus pour etre sur
            # qu'on n'a pas choppe un glitch :
            #
            do_step(1)
            reed_state=GPIO.input(o_sensor_fw)
            counter=counter+1
            #
            # et on s'arrete si apres les 3 pas on est toujours bien
            # la ou on veut aller
        if(counter==3):
            stop=True

    if step_pos>=LIMIT:
        fail_count=fail_count+1

    return step_pos

#
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
interactive=True
try:
    if sys.argv[1]!="":
        interactive=False
except:
    interactive=True

filter_index=0
fail_count=0

# olm_fw_fifoname is now defined in gpio_filter_assignments
# olm_fw_fifoname="/home/fmeyer/indi/fwfifo"

try:
    try:
        os.unlink(olm_fw_fifoname)
    except:
        pass
    fif=os.mkfifo(olm_fw_fifoname,0o600)
    fifofile = os.open(olm_fw_fifoname, os.O_RDONLY|os.O_NONBLOCK)
except:
    print ("Fifo error %s"%(olm_fw_fifoname))
    exit()
    pass


# filters=[" UNKNOWN ", "LUMINANCE", "   RED    ", "  GREEN   ", "  BLUE  ", "   Ha    "]
if interactive:
    stdscr = curses.initscr()
    curses.start_color()
    try:
        stdscr.curs_set(False)
        curses.curs_set(False)
    except:
        pass
    curses.noecho()
    s="    FILTER WHEEL "
    stdscr.addstr(0,0,s,curses.A_REVERSE)
    s="  POSITION   FILTER "
    stdscr.addstr(1,1,s,curses.A_BOLD)

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)

reed_sensor_on=1
reed_sensor_off=0
reed_state=-1

LIMIT=1000
step_count=0
step_inc=1
old_dir=1
step_pos=0
frequency=1600 # en Hz
duty_cycle=0.25
delay_step=duty_cycle/frequency
delay_steplow=(1.-duty_cycle)/frequency
delay_steplow=delay_step
usteps_per_step=8
offset_sensor=50*usteps_per_step
abs_pos=0
align_steps=40
out_steps=160
#
# GPIO pin assingnment in file piobs_gpio_assignments.py
#
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#
#
# GPIO pin dir settings
#
try:
    GPIO.setup(o_step_fw, GPIO.OUT)
except:
    old_dir=1

try:
    GPIO.setup(o_dir_fw, GPIO.OUT)
except:
    old_dir=1

try:
    GPIO.setup(o_enable_fw, GPIO.OUT)
except:
    old_dir=1

try:
    GPIO.setup(o_sensor_fw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    #GPIO.setup(o_sensor_fw, GPIO.IN)
except:
    old_dir=1
    sys.exit()
#
# GPIO pin init
#
GPIO.output(o_step_fw,GPIO.HIGH)
GPIO.output(o_dir_fw,GPIO.LOW)
GPIO.output(o_enable_fw,GPIO.LOW)

#
#
# saving term settings
#
if interactive:
    fd = sys.stdin.fileno()
    initial_settings = termios.tcgetattr(fd)
    _thread.start_new_thread(keypress, ())

# olm_fw_statefile is now defined in gpio_filter_assignments
# olm_fw_statefile="/home/fmeyer/filter_wheel_state"
try:
    with open(olm_fw_statefile,"r") as f:
        i,initstate,status=f.readline().split()
        initindex=int(i)

except:
    initindex=0

fail_count=0

pwr_stepper("ON")

reset_index()
#
# Init : find init index
#
count=0
while filter_index!=1 and fail_count==0:
    count=count+1
    do_step(out_steps)
    step_pos=0
    do_move(reed_sensor_off)
    if (fail_count>0):
        status_line(" reached LIMIT steps");
    else:
        status_line(" ** index off found %d step %d"%(reed_state,step_pos));

    if step_pos > 500 and step_pos < 600:
        do_move(reed_sensor_on)
        do_step(out_steps)
        do_move(reed_sensor_off)
        do_step(align_steps-40)
        init=True
        filter_index=1
        status_line(" init ok")

    if fail_count>0:
        status_line(" reached LIMIT steps");
    else:
        status_line(" count %d fail %d"%(count, fail_count));

seek_index(initindex)
if fail_count>0:
    status_line(" reached LIMIT steps");

if fail_count>0:
    filter_index=0
    status_line(" init failed (fw stepper off ?)")
    statusword="ERRSTEP"

while True:
    target=filter_index
    if interactive:
        if keycode==27:
            keycode=ord(getch())
            if keycode==91:
                keycode=ord(getch())
                if keycode==65 or keycode==67:   # up / right
                    seek_index(filter_index%5+1)
                elif keycode==66 or keycode==68: # down / left
                    seek_index((filter_index-2)%5+1)
                elif keycode==49: #
                    keycode=ord(getch())
                    if keycode==126:   # home
                        seek_index(1)
                elif keycode==52: #
                    keycode=ord(getch())
                    if keycode==126:   # end
                        seek_index(5)
        elif keycode==49 or keycode==50 or keycode==51 or keycode==52 or keycode==53:
            seek_index(keycode-48)
        elif keycode==3 or keycode == 113 or keycode == 81: # ctrl-c / q / Q
            clean_exit(2,0)
            break

        if keycode is not None:
            #print keycode
            keycode=None
            _thread.start_new_thread(keypress, ())

    if filter_index>5 or (filter_index>1 and step_pos<700): # cas pathologiques
        status_line("rollover...")
        reset_index()
        seek_index(filter_index)
    else:
        status_line("Ready")
        status_word="OK"
    #n=DateTime.now()
    update_statefile("READY")
    if fail_count!=0:
        status_line("Failed %d"%fail_count)
        statusword="ERRSTEP"

    time.sleep(0.05)

    try:
        string = os.read(fifofile, 32).decode().strip()
    except OSError as err:
        if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
            string = None
        else:
            raise  # something else has happened -- better reraise

    if string is None or string == "":
        index=filter_index
    else:
        try:
            index=int(string[0])
        except:
            try:
                index=int(string)
            except:
                if string=="STOP":
                    clean_exit(2,0)
    if index!=filter_index:
        seek_index(index)
pwr_stepper("OFF")

