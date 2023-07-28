#!/usr/bin/python3
# -*- coding: utf-8 -*
#.syrefv25 utf8

import cgi
import os
import sys
import subprocess 

sys.path.append(os.path.dirname(__file__)+"/../../websys")
from params import Params

class RelServPage:
    form = None
    server="/"
    status = ""
    lightstatus = 0

    def __init__(self, form):
        self.form = form

    def prodName(self):
        return 'RelayServer'

    def getHeaders(self):
        return "Content-type: text/html; charset=utf-8\n"

    def show(self):
        html  = "<!DOCTYPE html>\n"
        html += "<head>\n"
        html += "    <title>"+self.prodName()+" : "+self.getTitle()+"</title>\n"
        html += '    <link rel="stylesheet" type="text/css" href="../style.css" />\n'
        refreshSeconds = self.getRefreshSeconds()
        if refreshSeconds != None:
            html += '    <meta http-equiv="refresh" content="'+str(refreshSeconds)+';/page/relays.py" />\n'
        html += "</head>\n"
        html += "<body>\n\n"
        html += '<div id="header"  class="logobox">\n'
        html += '<div id="header-left">\n'
        html += '<span id="device"><a href="/page/relays.py">' +self.prodName()+" "+self.getTitle()+'</a></span>\n'
        #html += "<h1>"+self.prodName()+" : "+self.getTitle()+"</h1>\n\n"
        html += '</div>\n'
        html += '</div>\n'
        
        
#       html += '<div class="logobox">\n'
#       html += '<img src="/images/logoltfb.png">\n'
#       html += '<img src="/images/logo-gorgy-timing-fr-rvb.png">\n'
#       html += '</div>\n'
        
        html += '<div id="wrap">\n'

#       html += '<div class="menu">\n'
#       html += '    '+self.showLinkToPage('datafiles', 'Donn&eacute;es')+'\n'
#       html += '    '+self.showLinkToPage('gps', 'GPS')+'\n'
#       html += '    '+self.showLinkToPage('config', 'Configuration')+'\n'
#       html += '    '+self.showLinkToPage('certificats', 'Certificats')+'\n'
#       html += '    '+self.showLinkToPage('status', 'Status')+'\n'
#       html += '</div>\n\n'

        html += '<div class="main">\n'
        html += self.getPage()
        html += '</div>\n '
        html += '</div>\n '

        html += "</body>\n"
        html += "</html>\n"

        return self.getHeaders()+"\n"+html
    
    def getRefreshSeconds(self):
        return 30

    def showLinkToPage(self, pageID, label):    # warn : pageID & label not escaped
        if (pageID == self.pageID()):
            classes = "selected"
        else:
            classes = ""

        return '<a href="'+pageID+'.py" class="'+classes+'">'+label+'</a>'

    def showValue(self, label, fname):    # warn : label not escaped, fname : must be well known file
        content = 'None'
        classes = 'v na'
        try:
            with open(Params.getTmpDir()+fname, 'r') as content_file:
                content = content_file.read()
                classes = 'v'
        except IOError:
            pass

        return '<div><label for="'+fname+'">'+label+' :</label><span id="'+fname+'" class="'+classes+'">'+cgi.escape(content.strip())+'</span></div>\n'
    
    def cmd_syref_env(self, sy_cmd, *args) : #execute les commandes specifiques inclueses dans syref_env.sh
        cmd = 'source /etc/profile.d/syref_env.sh ; ' + sy_cmd + ' ' + ' '.join([str(i) for i in args])
        return os.popen(cmd)

    def runningRead(self, param) : #execute les commandes specifiques inclueses dans syref_env.sh
        try:
            with open(Params.getTmpDir()+param, 'r') as content_file:
                value = content_file.read().strip()
        except IOError:
            value=""
            pass
        return value

    def getIniEnv(self, var):
        cmdstream = self.cmd_syref_env("sy_get_inienv", var)
        value=cmdstream.readline().strip()
        cmdstream.close()
        return value

