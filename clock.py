#!/usr/bin/python3
import datetime
from jdcal import gcal2jd
from time import sleep
import os
import locale
import sys
import curses

stdscr = curses.initscr()
try:
    stdscr.curs_set(False)
    curses.curs_set(False)
except:
    pass
curses.noecho()
lang='fr'
tz='UTC'
os.putenv('TZ',tz)
os.putenv('LC_DATE',lang)
os.putenv('LC_TIME',lang)
os.putenv('LANG',lang)
os.putenv('LC_ALL',lang)
locale.setlocale(locale.LC_TIME,"fr_FR.UTF8")

olds=0
try:
    beep=sys.argv[1]
except:
    beep=None

gpsepoch=datetime.datetime(1980,1,6)
secsinweek=7*86400
while True:
    try:
        s=""
        sleep(0.11)
        n=datetime.datetime.now()
        s=s+"\n  %s %s\n"%(n.strftime("%H:%M:%S"),tz)
        
        if beep:
            sec=int(n.second)
            if sec != olds:
                if sec % 10 == 0:
                    if sec % 60 == 0:
                        os.system('beep -f 1055 -l 50;')
                    else:
                        os.system('beep -f 755 -l 50')
                else:
                    os.system('beep -f 555 -l 50')
            olds=sec

        wn=(n-gpsepoch).seconds/secsinweek
        jd=gcal2jd(n.year, n.month, n.day)
        mjd=float(jd[1])+(n.hour*3600+n.minute*60+n.second)/86400
        s=s+"  %s \n\n  MJD %11.5f\n"%(n.strftime("%A %d %m %Y ").strip(),mjd)
        s=s+"  DOY %3s\n  SEMAINE %2s \n  WN %d \n  UNIX %s"%(n.strftime("%j").strip(),n.strftime("%V").strip(),int(wn), n.strftime("%s").strip())
        try:
            stdscr.addstr(0,0,s,curses.A_BOLD)
        except:
            beep=None

        stdscr.refresh()
    except KeyboardInterrupt:
        curses.nocbreak(); 
        stdscr.keypad(0); 
        curses.echo()
        curses.endwin()
        sys.exit()
