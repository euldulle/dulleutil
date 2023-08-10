#!/usr/bin/python3
# -*- coding: utf8 -*
#.syrefv25 utf8

from _elems import *

import cgi
import os
import requests
import urllib
import urllib.request
from time import sleep
from re import sub

class RelayPage(RelServPage):
    kmtronic_bare='http://fmeyer:4so4xRg9@192.168.0.23/'
    kmtronic_status=kmtronic_bare+'relays.cgi'
    kmtronic_switch=kmtronic_bare+'relays.cgi?relay='
    kmtronic_config=[]

    relays=(
        {'relais':'Relay-01:', 'rank': '06', 'affect': 'FW Stepper', 'type': "cons"},
        {'relais':'Relay-02:', 'rank': '07', 'affect': 'C14 Stepper', 'type': "cons"},
        {'relais':'Relay-03:', 'rank': '08', 'affect': 'TS Stepper', 'type': "cons"},
        {'relais':'Relay-04:', 'rank': '00', 'affect': 'NA', 'type': "cons"},
        {'relais':'Relay-05:', 'rank': '00', 'affect': 'NA', 'type': "cons"},
        {'relais':'Relay-06:', 'rank': '00', 'affect': 'NA', 'type': "cons"},
        {'relais':'Relay-07:', 'rank': '00', 'affect': 'NA', 'type': "cons"},
        {'relais':'Relay-08:', 'rank': '00', 'affect': 'NA', 'type': "cons"},
        {'relais':'Relay-09:', 'rank': '04', 'affect': 'Dew Heater', 'type': "cons"},
        {'relais':'Relay-10:', 'rank': '03', 'affect': 'Oid', 'type': "cons"},
        {'relais':'Relay-11:', 'rank': '05', 'affect': 'Atik', 'type': "cons"},
        {'relais':'Relay-12:', 'rank': '01', 'affect': 'USB HUB', 'type': "cons"},
        {'relais':'Relay-13:', 'rank': '02', 'affect': 'EQ8', 'type': "cons"},
        {'relais':'Relay-14:', 'rank': '14', 'affect': 'Close Roof', 'type': "temp"},
        {'relais':'Relay-15:', 'rank': '15', 'affect': 'Stop Roof', 'type': "temp"},
        {'relais':'Relay-16:', 'rank': '16', 'affect': 'Open  Roof', 'type': "temp"}
        )

    filters=(
        {'pos':'0', 'filter': 'UNK', 'color': '#808080', 'type': "cons"},
        {'pos':'1', 'filter': 'LUM', 'color': '#FFFFFF', 'type': "cons"},
        {'pos':'2', 'filter': 'RED', 'color': '#FF0000', 'type': "cons"},
        {'pos':'3', 'filter': 'GRN', 'color': '#00FF00', 'type': "cons"},
        {'pos':'4', 'filter': 'BLU', 'color': '#0000FF', 'type': "cons"},
        {'pos':'5', 'filter': 'HA',  'color': '#800080', 'type': "cons"}
       )

    delay=1.0

    def pageID(self):
        return 'relay'

    def getTitle(self):
        return '16 port'

    def sessionControl(self):
        self.status='<div class="column"><table>'
        self.status += '<thead> <tr><th colspan="4" align="center"> <font color="#444488"> Session control</font></th></tr></thead>\n'

        self.status += '<tr><td style="text-align:center;"><a href="/page/relays.py?session=coldstart" title="Init session">'
        self.status += '<font color="#0000FF">Init session</font></a></td></tr>'
        self.status += '<tr><td style="text-align:center;"><a href="/page/relays.py?session=shutdown" title="Shutting down everything">'
        self.status += '<font color="#0000FF">Shutdown</font></a></td></tr>'
        self.status += '<tr><td style="text-align:center;"><a href="/page/relays.py?session=timesync-eq8" title="sync mount to UTC">'
        self.status += '<font color="#0000FF">Time sync EQ8</font></a></td></tr>'
        self.status += '</table>\n'
        self.status += '</div>'
        self.status += '<br/>\n'
        return self.status

    def getIndiStatus(self):
        #
        self.status='<div class="column"><table>'
        self.status += '<thead> <tr><th colspan="4" align="center"> <font color="#444488"> Indi server/driver</font></th></tr></thead>\n'
        #self.status += '<tr><td colspan="4"> <font color="#FF0000">cant get indi status (192.168.0.26 off ?)</font></td>\n'
        if True:
            p=subprocess.Popen([Params.getObslmDir()+'obslm.bash olm_get_indi_status'],stdout=subprocess.PIPE,shell=True)
            if p.stdout.readline().decode('utf-8').rstrip() == "notup":
                self.status += '<tr><td colspan="4"> <font color="#FF0000">cant get indi status (192.168.0.26 off ?)</font></td>\n'
            else:
                for line in p.stdout:
                    sline=line.decode('utf-8')
                    indistatus=sline.split()

                    cyclecom='olm_in_cycle %s'%(indistatus[0])
                    stopcom='olm_in_stop %s'%(indistatus[0])
                    startcom='olm_in_start %s'%(indistatus[0])

                    self.status += '<tr><td> <font color="#0000FF">'+indistatus[0]+'</font></td>\n'

                    if  (indistatus[2] == 'not_running'):
                        self.status += '<td> <font color="#FF0000">NOTUP</font></td>\n'
                    else:
                        self.status += '<td><font color="#00B000">'+indistatus[2] + '</font></td>\n'


                    if  (indistatus[2] == 'not_running'):
                        self.status += '<td style="text-align:center;" colspan=2> <a href="/page/relays.py?indicom=olm_in_start&inditarget='+indistatus[0]+'">Start</a></td>\n'
                    else:
                        self.status += '<td > <a href="/page/relays.py?indicom=olm_in_stop&inditarget='+indistatus[0]+'">Stop</a></td>\n'
                        self.status += '<td > <a href="/page/relays.py?indicom=olm_in_cycle&inditarget='+indistatus[0]+'">Cycle</a></td>\n'
                    self.status += '</tr>\n'
        self.status += '</table>\n'
        self.status += '<br/>\n'

 #####    ###   #####
#     #    #    #    #
#     #    #    #     #
#     #    #    #     #
#     #    #    #     #
#     #    #    #    #
 #####    ###   #####

        self.status += '<table>\n'
        self.status += '<thead> <tr><th colspan="4" align="center"> <font color="#444488"> Single boards control</font></th></tr></thead>\n'

        self.status += '<tr><td colspan="2"><font color="#008000">Oid</font></td>'
        self.status += '<td style="text-align:center;"><a href="/page/relays.py?reboot=indi"><font color="#0000FF">reboot</font></a></td>'
        self.status += '<td style="text-align:center;"><a href="/page/relays.py?shutdown=indi">shutdown</a></td></tr>\n'

        self.status += '</table>'
        self.status += '<br/>\n'

#######         #     # #     # ####### ####### #
#               #  #  # #     # #       #       #
#               #  #  # #     # #       #       #
#####           #  #  # ####### #####   #####   #
#               #  #  # #     # #       #       #
#               #  #  # #     # #       #       #
#       #######  ## ##  #     # ####### ####### #######

        self.status += '<table>\n'
        self.status += '<thead> <tr><th colspan="4" align="center"> <font color="#444488"> Filter Wheel</font></th></tr></thead>\n'

        p=subprocess.Popen([Params.getObslmDir()+'obslm.bash olm_fw_get_filter'],stdout=subprocess.PIPE,shell=True)
        fwline=p.stdout.readline().decode('utf-8').rstrip()
        if fwline == "notup" or fwline == "" or fwline == None:
            self.status += '<tr><td colspan="2">\n'
            self.status += '<font color="#FF0000">cant get fw status (192.168.0.26 off ?)</font></td>\n'
        else:
            fwstatus=fwline.split()
            self.status += '<tr><td colspan="2">\n'
            self.status += '<font color="#FF0000">%s</font></td>\n'%fwstatus[2]

            filt=self.filters[int(fwstatus[0])]

            #for i in range (1,5):
            #    fwsetcom[i]='fw_set %d'%(i)

            self.status += ('<tr><td>Current : </td><td> <font color="'
                    +filt['color']+'">'+filt['filter']+'</font></td></tr>\n')

#               if  (fwstatus[2] == 'not_running'):
#                   self.status += '<td> <font color="#FF0000">NOTUP</font></td>\n'
#               else:
#                   self.status += '<td><font color="#00B000">'+filters[] + '</font></td>\n'
            for f in self.filters:
                pos=f['pos']
                if pos!='0':
                    self.status+= '<tr><td>Select :</td>'
                    self.status += '<td>'
                    if pos==filt['pos']:
                        self.status += '<font color="'+filt['color']+'">'+filt['filter']+'</font></td>'
                    else:
                        self.status += '<a href="/page/relays.py?fwset='+pos+'" style="color: '+f['color']+'">'+f['filter']+'</font></a></td>'

            self.status += '</tr>\n'

        self.status += '</table>'
        self.status += '</div>'
        return self.status

    def getFWStatus(self):
        pass

    def getRelayStatus(self):
        #
        # get status for box 2, the chinese one.
        #
        self.status='<div class="column"><table>'
        self.status += '<thead> <tr><th colspan="2" align="center"> <font color="#444488"> 16-RELAY BOX</font></th></tr></thead>\n'
        self.lines=[]
        p=subprocess.Popen([Params.getObslmDir()+'obslm.bash olm_get_relay_state 16'],stdout=subprocess.PIPE,shell=True)
        #
        # Output of the command :
        #   get_relay_state.bash 16
        #
        # OK
        # Relay-01: ON http://relais16/30/00
        # Relay-02: OFF http://relais16/30/03
        # Relay-03: OFF http://relais16/30/05
        # Relay-04: OFF http://relais16/30/07
        # Relay-05: OFF http://relais16/30/09
        # Relay-06: OFF http://relais16/30/11
        # Relay-07: OFF http://relais16/30/13
        # Relay-08: OFF http://relais16/30/15
        # Relay-09: ON http://relais16/30/16
        # Relay-10: ON http://relais16/30/18
        # Relay-11: OFF http://relais16/30/21
        # Relay-12: OFF http://relais16/30/23
        # Relay-13: OFF http://relais16/30/25
        # Relay-14: OFF http://relais16/30/27
        # Relay-15: OFF http://relais16/30/29
        # Relay-16: OFF http://relais16/30/31

        if p.stdout.readline().decode('utf-8').rstrip()== "OK":
            for line in p.stdout:
                sline=line.decode('utf-8')
                splitrelay=sline.split()
                relay=splitrelay[0]
                state=splitrelay[1]

                color='<font color="#0000FF">??</font>'
                if (state == "ON"):
                    color='<font color="#00B000">ON</font>'

                if (state == "OFF"):
                    color='<font color="#FF0000">OFF</font>'

                switchref=splitrelay[2]
                # sort=sorted(self.relays, key=lambda k: k['affect'])
                for rel in self.relays:
                    if relay in rel.values():
                        if (rel['affect']!="NA"):
                            #
                            # on ignore les relais non affectes
                            # rappel structure dictionnaire self.relays :
                            # {'relais':'Relay-01:',    nom du relais
                            #  'rank': '06',            son rang dans la page affichee
                            #  'affect': 'FW Stepper',  son affectation
                            #  'type': "cons"}          son type (cons (switch) ou temp (push))

                            newline=('<tr><td title="'
                                + rel['rank']
                                + '"><a href="/page/relays.py?switch='
                                + switchref
                                + '">\n'
                                + rel['affect'] +'</a>\n')
                            if (rel['affect']=="Open  Roof" or rel['affect']=="Close Roof"):
                                #
                                # pour les actions open et close roof, on prévoit une
                                # version normale (une seule action start)
                                # et une version courte (une action start suivie d'une action stop)
                                newline +=('<a title="short" href="/page/relays.py?switch='
                                            + switchref
                                            +'&action=short">/ (short)</a>\n')
                            newline += '</td><td style="text-align:center;">'+color+'</td>\n'
                            newline += '</tr>'
                            self.lines.append(newline)
            #
            # on trie les entrees pour les presenter dans l'ordre specifie dans la cle 'rank' :
            #
            sort=sorted(self.lines)
            for line in sort:
                self.status += line
        else:
            self.status += '<tr><td colspan="2"> <font color="#FF0000">cant get 16-relay status</font></td></tr>\n'

        self.status += '</table><br>\n'
        self.status += '<table>\n'
        self.status += '<thead> <tr><th colspan="2" align="center"> <font color="#444488"> 8-RELAY BOX</font></th></tr></thead>\n'

        #
        # getting status from kmtronic box, the bulgarian one
        #
        p=subprocess.Popen([Params.getObslmDir()+'obslm.bash olm_get_relay_state 8'],stdout=subprocess.PIPE,shell=True)
        etat=p.stdout.readline().decode('utf-8').rstrip()
        if etat == "OK":
            line=p.stdout.readline()
            self.kmtronic_status=line.decode('utf-8').split()

            for line in p.stdout:
                self.kmtronic_config.append(line.decode('utf-8').lstrip().rstrip())

            for config, status in zip(self.kmtronic_config, self.kmtronic_status):
                if config != "NA":
                    color='<font color="#00B000">'+status+'</font>'
                    if (status == "1"):
                        color='<font color="#00B000">ON</font>'
                        setstate=0

                    if (status == "0"):
                        color='<font color="#FF0000">OFF</font>'
                        setstate=1

                    self.status += '<tr><td> <a href="'
                    #self.status += '/page/relays.py?switch=%d>%s</a></td><td style="text-align:center;" >'%(1+self.kmtronic_config.index(config),config)
                    self.status += '/page/relays.py?switch=%d&setstate=%d">%s</a></td><td style="text-align:center;" >'%(1+self.kmtronic_config.index(config),setstate,config)
                    self.status += color+'</td></tr>\n'
                else:
                    pass
                    #self.status += '<tr><td colspan="4"> supposedly NA '+config+' ' + status +'</font></td></tr>\n'
        else:
            self.status += '<tr><td colspan="4"> <font color="#FF0000">cant get 8-relay status</font></td></tr>\n'
        #
        # end getting status from kmtronic box, the bulgarian one
        #

        self.status += "</table></div>\n"
        return self.status

    def getPage(self):
        page = ''
        page += '<div class="row">'

        if "session" in form:
            action=form.getvalue('session')
            if action == "coldstart":
                command=Params.getObslmDir()+'obslm.bash olm_cold_init force'
                p=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
                form['session'].value='None'
                sleep(self.delay)

            if action == "shutdown":
                page += '<div> Shutdown everything <a href=/page/relays.py?session=shutdown-confirm>Confirm</a></div>'
                page += '</div>'
                return page

            if action == "shutdown-confirm":
                p=subprocess.Popen([Params.getObslmDir()+'obslm.bash olm_session_shutdown'],stdout=subprocess.PIPE,shell=True)
                form['session'].value='None'
                sleep(self.delay)

            if action == "timesync-eq8":
                command=Params.getObslmDir()+'obslm.bash olm_indicmd olm_in_sync_eq8_time force'
                p=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
                form['session'].value='None'
                sleep(self.delay)

        if "switch" in form:
            try:
                url=form.getvalue('switch')
                try:
                    #
                    # address the 8-switch actions
                    #
                    # if url is just an int then its a command for 8-relay Box
                    switch8=int(url)
                    newurl=self.kmtronic_switch+url
                    p=subprocess.Popen(['wget -O/dev/null >/dev/null 2>/dev/null '+ newurl],stdout=subprocess.PIPE,shell=True)
                except:
                    #
                    # address the 16-switch actions
                    #

                    urllib.request.urlretrieve(url,filename="/dev/null")
                    request = url[-2:]
                    intreq = int(request)

                    rel = self.relays[int(intreq/2)]
                    if rel['type'] == 'temp':
                        if intreq % 2 == 0:
                            opreq = intreq + 1
                        else:
                            opreq = intreq - 1
                        sleep(self.delay)

                        newurl=sub("%s$" %request, "%.2d"%opreq, url)
                        urllib.request.urlretrieve(newurl,filename="/dev/null")

                    if "action" in form:
                        sleep(1)
                        #
                        # Sending stop
                        #
                        urllib.request.urlretrieve("http://relais16/30/29",filename="/dev/null")
                        sleep(self.delay)
                        urllib.request.urlretrieve("http://relais16/30/28",filename="/dev/null")

            except:
                page = "error urllib"
                page = "Unexpected error:", sys.exc_info()[0]
                raise
            form['switch'].value='None'

        if "shutdown" in form:
            try:
                target=form.getvalue('shutdown')
                if (target  == "pio"):
                    command='sudo poweroff'

                if (target  == "indi"):
                    command=Params.getObslmDir()+'obslm.bash olm_indicmd sudo poweroff'

                p=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
                sleep(self.delay)

            except:
                page = "shutdown "
                page = "Unexpected error:", sys.exc_info()[0]
                raise

            form['shutdown'].value='None'

        if "reboot" in form:
            try:
                target=form.getvalue('reboot')
                if (target  == "pio"):
                    command='sudo reboot'

                if (target  == "indi"):
                    command=Params.getObslmDir()+'obslm.bash olm_indicmd sudo reboot'

                p=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
                sleep(self.delay)

            except:
                page = "reboot "
                page = "Unexpected error:", sys.exc_info()[0]
                raise

            form['reboot'].value='None'

        if "fwset" in form:
            try:
                target=int(form.getvalue('fwset'))

                if (target >0 and target <6):
                    command=Params.getObslmDir()+"obslm.bash olm_indicmd olm_fw_set %d"%target

                p=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
                sleep(2)

            except:
                page = "fwset "
                page = "Unexpected error:", sys.exc_info()[0]
                raise

            form['fwset'].value='None'

        if "indicom" in form:
            try:
                indicom=form.getvalue('indicom')
                try:
                    inditarget=form.getvalue('inditarget')
                except:
                    inditarget=''
                if (inditarget == None):
                    inditarget=''
                command=Params.getObslmDir()+'obslm.bash olm_indicmd '+ indicom + ' ' + inditarget
                p=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
                if p.returncode !=0:
                    p=False

                sleep(self.delay)

            except:
                page = "indicom "
                page = "Unexpected error:", sys.exc_info()[0]
                raise
            form['indicom'].value='None'
            form['inditarget'].value='None'

        page += self.getRelayStatus()
        page += self.sessionControl()
        page += self.getIndiStatus()
        page += '</div>'
        return page

    def getRefreshSeconds(self):
        return 10

form = cgi.FieldStorage()

page = RelayPage(form)
print(page.show())
