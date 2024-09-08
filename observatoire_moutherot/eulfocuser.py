#!/usr/bin/python
#
# The hardware part of the indi_eul_focuser
#
# aiming at reading the hands of a mitutoyo indicator
# and spitting out the results to a udp client
#           FM 20240823
import time
import socket
from picamera2 import Picamera2
import cv2
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sys import argv

global isroic,ilroic,testing,udp_socket
rep="/data/mitutoyo/"
sroi = (592, 72, 300, 300)  # Replace with actual ROI for small hand
lroi = (332, 196, 600, 600)  # Replace with actual ROI for large hand
centerLroi=(int(lroi[2]/2),int(lroi[3]/2))
centerSroi=(int(sroi[2]/2),int(sroi[3]/2))
smallContourRange = (380, 620)
largeContourRange = (800, 1100)
largeContourRangeDegraded = (700, 820)


rois = [sroi, lroi]
# Filter contours based on length
small_hand_contours = []
large_hand_contours = []
cx=int(0)
cy=int(0)
    
def init_udp_broadcast():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return udp_socket

def udp_broadcast(socket,message,port):
    socket.sendto(message.encode(), ('255.255.255.255', port))

def ps(v1,v2):
    return np.sign(v1[0]*v2[0]+v1[1]*v2[1])

# Function to detect hands and calculate angles
def detect_small_hand(image,contourRange):
    # Find contours for small hand
    small_hand_contours,hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if testing:
        saveimg(image,"smallcontours")

    small_tirage=99
    for contour in small_hand_contours:
        # Calculate length of contour
        length = cv2.arcLength(contour, True)
        # print("small length: %f"%length)

        # Filter based on length range
        if testing:
            print("small length: %f"%length)
        if length >= contourRange[0] and length <= contourRange[1]:
            if cv2.pointPolygonTest(contour,centerSroi,False)>0:
                small_angle=get_principal_axis(contour,isroic,sroi)
                if (small_angle<-5):
                    small_angle+=360
                small_tirage=small_angle/360*10
                break
                #print (datetime.now()," small tirage %6.3f"%small_tirage)

    return small_tirage,small_hand_contours

def detect_large_hand(image, contourRange):
    global cx,cy,ellipse,rect

    # Find contours for small hand
    large_hand_contours,hierarchy = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if testing:
        saveimg(image,"largecontours")

    large_tirage=99
    for contour in large_hand_contours:
        # Calculate length of contour
        length = cv2.arcLength(contour, True)
        if testing:
            print("large length: %f"%length)

        # Filter based on length range
        #if cv2.pointPolygonTest(contour,centerLroi,False)>0:
        if length >= contourRange[0] and length <= contourRange[1]:
            if cv2.pointPolygonTest(contour,centerLroi,False)>0:
                large_angle=0-get_principal_axis(contour,ilroic,lroi)
                if large_angle<0:
                    large_angle+=360
                large_tirage=large_angle/360
                break
                #print (datetime.now()," large tirage %6.3f"%large_tirage," angle %6.2f"%large_angle)
                #print (datetime.now()," large tirage %6.3f"%large_tirage," angle %6.2f"%large_angle)

    return large_tirage,large_hand_contours

# Function to convert angles to distances
def angles_to_distances(small_hand_angle, large_hand_angle):
    # Calculate distances based on angle and indicator properties

    return small_hand_distance, large_hand_distance

def draw_rois_on_image(image):
    # Make a copy of the image to draw on
    image_with_rois = image.copy()

    for roi in rois:
        x, y, w, h = roi
        # Draw rectangle around ROI
        cv2.rectangle(image_with_rois, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return image_with_rois

def draw_axis(img, p, q, color, scale):
    angle = np.arctan2(p[1] - q[1], p[0] - q[0])
    hypotenuse = np.sqrt((p[1] - q[1])**2 + (p[0] - q[0])**2)
    q = (p[0] - scale * hypotenuse * np.cos(angle),
         p[1] - scale * hypotenuse * np.sin(angle))
    p = tuple(map(int, p))
    q = tuple(map(int, q))
    cv2.line(img, p, q, color, 1, cv2.LINE_AA)
    p = (q[0] + 9 * np.cos(angle + np.pi / 4),
         q[1] + 9 * np.sin(angle + np.pi / 4))
    cv2.line(img, q, tuple(map(int, p)), color, 1, cv2.LINE_AA)
    p = (q[0] + 9 * np.cos(angle - np.pi / 4),
         q[1] + 9 * np.sin(angle - np.pi / 4))
    cv2.line(img, q, tuple(map(int, p)), color, 1, cv2.LINE_AA)

def get_principal_axis(contour, imroic, roi):
    data = np.array(contour, dtype=np.float64).reshape(-1, 2)
    mean, eigenvectors, eigenvalues = cv2.PCACompute2(data, mean=None)
    principal_axis = eigenvectors[0]
    pa1x=int(roi[2]/2+principal_axis[0]*100)
    pa1y=int(roi[3]/2+principal_axis[1]*100)

    (ccx,ccy),radius = cv2.minEnclosingCircle(contour)
    ccenter=(int(ccx),int(ccy))
    imcenter=(int(roi[2]/2),int(roi[3]/2))
    if testing:
        cv2.circle(imroic,ccenter,int(radius),(0,0,255),2)
        cv2.line(imroic,imcenter,ccenter,(0,255,0),2)
        cv2.line(imroic,imcenter,(pa1x,pa1y),(255,0,0),2)
    prods=ps(((ccenter[0]-imcenter[0]),(ccenter[1]-imcenter[1])),(principal_axis))
    angle = np.arctan2(principal_axis[1]*prods,principal_axis[0]*prods)  # angle in radians
    angle_degrees = 90-np.degrees(angle)  # optional: convert the angle to degrees
    return angle_degrees

def saveimg(image,name):
    cv2.imwrite(f"%s/%s.jpg"%(rep,name), image)
    return

def imroi(image,roi):
    return image[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]

# Main function
def main():
    global isroic,ilroic,testing

    udp_socket=init_udp_broadcast()
    udpport=2345

    count=0
    small=99
    large=99

    testing=False
    if len(argv)>1:
        testing=True
    # Capture image using Raspberry Pi camera
    cv2.startWindowThread()

    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1280, 960)}))
    picam2.start()
    image = picam2.capture_array()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #for i in range(10,250,10):
    #    _, thresh = cv2.threshold(gray, i, 255,  cv2.THRESH_BINARY_INV )
    #    tlroi = imroi(thresh, lroi)
    #    tsroi = imroi(thresh, sroi)
    #    saveimg(tlroi,"large%.3d"%i)
    old=time.time()

    while True:
        status=3
        #
        #
        # acquisition image
        #
        image = picam2.capture_array()
        #
        #
        # dessin ROI large and small
        #
        if testing:
            imroi_i=draw_rois_on_image(image)
        #
        #
        # sauvegarde image avec ROIs
        #
        if testing:
            saveimg(imroi_i,"rois")
        #
        #
        # extraction ROIs
        #
        ilroi = imroi(image, lroi)
        ilroic = ilroi.copy()
        isroi = imroi(image, sroi)
        isroic = isroi.copy()
        if testing:
            saveimg(ilroi,"lroi")
        #
        #
        # conversion image en niveau
        #
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        #
        # erosion :
        #   Creating kernel
        kernel = np.ones((3, 3), np.uint8)
        if testing:
            saveimg(gray,"large")

        tsroi = imroi(gray, sroi)
        _, tsroi = cv2.threshold(tsroi, 140, 255,  cv2.THRESH_BINARY_INV)
        tsroi = cv2.dilate(tsroi, kernel,iterations=1)
        tsroi = cv2.erode(tsroi, kernel, iterations=2)
        if testing:
            saveimg(tsroi,"small")

        newsmall,s_contours=detect_small_hand(tsroi,smallContourRange)

        # Draw contours on the image
        if testing:
            cv2.drawContours(isroic, s_contours, -1, (0, 255, 255), 2)
            saveimg(isroic,"scontours")

        #   Using cv2.erode() method
        tlroi = imroi(gray, lroi)
        _, tlroi = cv2.threshold(tlroi, 140, 255,  cv2.THRESH_BINARY_INV )
        tlroi = cv2.dilate(tlroi, kernel,iterations=1)
        tlroi = cv2.erode(tlroi, kernel,iterations=8)
        if testing:
            saveimg(tlroi,"large")

        contourRange=largeContourRange
        if (newsmall==99):
            cv2.circle(tlroi,centerLroi,275,(0,0,0),50)
            contourRange=largeContourRangeDegraded

        newlarge,l_contours=detect_large_hand(tlroi,contourRange)
        if (newsmall<99):
            small=newsmall
            status-=1

        if (newlarge<99):
            large=newlarge
            status-=2

        if (newlarge>1):
            newlarge-=1


        final=np.floor(small)+large
        if final-small>0.5:
            final-=1

        if final-small<-0.5:
            final+=1

        final=11-final

        new=time.time()
        elapsed=new-old
        #print (datetime.now()," final %6.3f (large %6.3f"%(final,large)," small %6.3f)\r"%small,end="")
        message="%+07.3f %+07.3f %+07.3f %d"%(final,large,small,status)

        if (elapsed > .1):
            print (message,"%.3f\r"%elapsed,end="")
            udp_broadcast(udp_socket,message,udpport)
            old=new

        # Draw contours on the image
        if testing:
            cv2.drawContours(ilroic, l_contours, -1, (0, 255, 255), 2)
            saveimg(ilroic,"lcontours")

        count=count+1
        if count%100==0:
            print (datetime.now())
            #testing=True
        else:
            testing=False


if __name__ == "__main__":
    main()
