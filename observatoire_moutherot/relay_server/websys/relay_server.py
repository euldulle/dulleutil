#!/usr/bin/python3
# -*- coding: utf-8 -*
#.syrefv25 utf8

import http.server
import socket
import os

from params import Params

#sys.path.append("../../websys")
# é
print()
print(Params.showServerParams())

os.chdir("../web")

with open(Params.getServerPIDfile(),'w') as f:
    f.write("%d"%(os.getpid()))

port = Params.getHttpPort()

handler = http.server.CGIHTTPRequestHandler
handler.cgi_directories = ["/page"]

httpd = http.server.HTTPServer(("", port), handler)

print("Serveur actif sur le port :", port)
httpd.serve_forever()
