#!/usr/bin/python3
import sys, re, email
from email.parser import BytesParser, Parser
from email.policy import default
import dateutil.parser

# logfile : 
#    an external tail -f logfile will display logs
logfile="/home/fmeyer/log/maillog"
# 
with sys.stdin.buffer as input_stream:
    #
    # first parse headers :
    headers = BytesParser(policy=default).parse(input_stream)
    headers
    #
    # then pass everything to stdout
    sys.stdout.buffer.write(headers.as_bytes())

ldate=8 
lsubj=56 
lfrom=56
lfold=12
rformat=str("| %%%ds | %%-%ds | %%-%ds | %%-%ds |"%(ldate, lsubj, lfrom, lfold))
dt = dateutil.parser.parse(format(headers['date']))
date=str(dt.astimezone(dateutil.tz.UTC).strftime("%H:%M:%S"))

bogofilter_headers = headers.get_all('X-Bogosity')
if bogofilter_headers[0].find('Spam')<0 and bogofilter_headers[0].find('nsure')<0:
    # processing non-spam
    recipient_folders={
        '.*fripon.org':'fripon', 
        '.*frequency-time-seminar':'efts',
        '.*etalonnages@obs-besancon.fr':'etalonnages',
        '.*contact@ltfb.fr':'etalonnages',
        '.*credmut@dulle.fr':'credmut',
        '.*mbi@dulle.fr':'mbi',
        '.*time-nuts@lists.febo.com':'time-nuts',
        '.*@dulle.fr':'dulleperso',
        '.*dulle@free.fr':'dulleperso',
        '.*gpsmaster':'gpsmaster',
        '.*obs@obs-besancon.fr':'obs', 
        '.*skychart':'skychart', 
        '.*ntp-adm':'ntp-adm',
        '.*raccord@':'gpsmaster',
        '.*root@ltfb':'gpsmaster'
        }
    
    sender_folders={
        '.*fripon.org':'fripon', 
        '.*frequency-time-seminar':'efts'
        }

    folder=None
    recipients = headers.get_all('to', []) + headers.get_all('cc', [])
    sender = headers.get_all('from', [])
    for recipient in recipients:
        recipient_address = email.utils.parseaddr(recipient)[1]  # Extract the email address

        # Check if the recipient matches any pattern in the recipient_folders dictionary
        for pattern, folder_name in recipient_folders.items():
            if re.match(pattern, recipient_address):
                folder = folder_name
                break  # Stop iterating if a match is found

        if folder:
            break  # Stop iterating if a match is found

    if folder==None:
        folder="dulle"

    with open(logfile, "a+") as fp:
        print(rformat%(date,format(headers['subject'])[0:lsubj-1], format(headers['from'][0:lfrom-1]), folder),file=fp)

#        if folder:
#            print (str(folder),file=fp)

#print (str(format(headers['from'])))
#print (str(format(headers['to'])))
#print (str(format(headers['cc'])))
sys.exit(0)

