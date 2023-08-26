#!/usr/bin/python3
# -*- coding: utf-8 -*
#.syrefv25 utf8

import socket
import os

class Params:
    hostname = socket.gethostname()
    root_dir="/home/fmeyer/observatoire_moutherot/relay_server/"
    obslm_dir="/home/fmeyer/observatoire_moutherot/"
    tmp_dir = "/tmp/"
    server_pid_file = tmp_dir+"relay.pid"
    data_dir = root_dir
    res_dir = root_dir
    #http_port = 8028
    http_port = 80
    box1_address = "192.168.1.23"
    box1_port = 80
    box2_address = "192.168.1.28"
    box2_port = 80
    box2_urlbase = "/30/"
    hostname = None

    @staticmethod
    def showServerParams():
        # ééé
        o  = 'hostname is "'+socket.gethostname().strip()+'"\n'
        o += 'tmp_dir = "'+Params.tmp_dir+'"\n'
        o += 'server_pid_file = "'+Params.server_pid_file+'"\n'
        o += 'data_dir = "'+Params.data_dir+'"\n'
        o += 'http_port = '+str(Params.http_port)+'\n'
        return o

    @staticmethod
    def getTmpDir():
        return Params.tmp_dir

    @staticmethod
    def getObslmDir():
        return Params.obslm_dir

    @staticmethod
    def getServerPIDfile():
        return Params.server_pid_file

    @staticmethod
    def getSatSuivisDir():
        return Params.getTmpDir()

    @staticmethod
    def getRamDataFilesDir():
        return Params.getTmpDir()

    @staticmethod
    def getSatVisiblesDir():
        return Params.getTmpDir()

    @staticmethod
    def getDataFilesDir():
        return Params.data_dir

    @staticmethod
    def getResDir():
        return Params.res_dir

    @staticmethod
    def getHttpPort():
        return Params.http_port
