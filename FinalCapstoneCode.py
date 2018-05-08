from findingCircles import compute, readFile
from calculatingDistances import getCartCoords, getDistance, getFocalLength, getPixWidth
from normalizeDist import normDistance
import server_thread
from logger import getLog
import cv2
import numpy as np
import time
import threading
import queue
import multiprocessing
import sys
import io
import socket
import struct
from PIL import Image
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plot

import os, shutil

all_clients_connected=False
program_terminated=False

## Adresses of Pis ##
# addresses=["169.254.118.241__"]
focal_lengths=[481]
addresses=["192.168.0.54__"]
#addresses=["169.254.118.241__, 169.254.28.103__,169.254.131.184__,169.254.151.41__"]
# focal_lengths[1262,1296,1274,1286]

############ Order is camera 1:(x,y,z), camera 2:(x,y,z).....################ 
normDist=[0,0,0]


## 1 ClientThread per Pi connected
class ClientThread(threading.Thread):
    global all_clients_connected, program_terminated
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.address = clientAddress
        print ("New connection added: ", self.address)
        
    def run(self):
        # print ("Connection opened: ", clientAddress)
        count=0
        imageNum=0
        connection = self.csocket.makefile('rb')

        while all_clients_connected==False:
            time.sleep(0.1)

        print ("Pi: "+ self.address[0] + " begin")
        while program_terminated==False:
            # Receive size of each image
            size = struct.unpack('<Q',connection.read(struct.calcsize('<Q')))[0]    # receive image size
            # Break loop when client sends 0-length byte
            if size==0:
                print('Received %d images from %s' % (count,(self.address[0])))
                break  
            # Put image data into byte stream, open & save to file
            imageNum = struct.unpack('<Q',connection.read(struct.calcsize('<Q')))[0]    # receive image index number
            print("imageNum: %d\tImageSize: %d\t Pi: %s" % (imageNum,size,self.address[0]))
            image_stream = io.BytesIO()
            image_stream.write(connection.read(size))      # receive image as byte stream
            image_stream.seek(0)
            image = Image.open(image_stream)
            image.save('images/%s__%d.jpg' % ((self.address[0]),imageNum))  # save image to images folder with filename
            count += 1
            
        print ("Client ", clientAddress , " disconnected...")
        self.csocket.close()
        print("Socket closed")

def findingDistance(calibration,dist,q2,q3,focal_length):
    trueWidth=2.3929 #inches
    circles=q2.get()[0]
    #print ("Circles are", circles)

    if circles[0,0] < 1:
        #distance=None
        #angle=None
        x=0
        y=0
        z=0
        q3.put(x)
        q3.put(y)
        q3.put(z)
        print("Determined distance from camera in format (x,y,z) is",x,y,z)
    else:
        #print("circles are, ", circles)
        circlesCopy=circles
        pixWidth=getPixWidth(circles)
        if calibration:
            focalLength=getFocalLength(dist,trueWidth,pixWidth)
            print("Calibrated Focal Length is", focalLength)
        else:
            # print("This is the focal length", focal_length)
            distance=getDistance(trueWidth,focal_length,pixWidth)
            [x,y,z]=getCartCoords(circlesCopy,distance,pixWidth)
            q3.put(x)
            q3.put(y)
            q3.put(z)
            print("Determined distance from camera in format (x,y,z) is ",x,y,z)
            print("\n")


def signalProcessingMethod(fName,q1,q2,q3,calibration,dist,focal_length):
    global program_terminated
    """ Create a thread for the reading in and wait for it to return its value 
    if the image queue is empty. Once the value is returned start the thread 
    for the computation part. Distance finding thread starts once q2, which has the output circle (x,y,radius), 
    is not empty and puts distance and angle onto queue 3"""
    highThresh=200
    lowThresh=50
    accumulatorThresh=5
    count=1
    #Setup
    t4=time.time()

    #create readThread obj
    readThread=threading.Thread(target=readFile, args=(fName,q1))
    readThread.start()
    # print("readThread started. Active threads: ", threading.active_count())
    #create computationThread obj
    computeThread=threading.Thread(target=compute, args=(q1,q2,highThresh,lowThresh, accumulatorThresh,count))
    if q1.empty():
        readThread.join()
    computeThread.start()
    # print("computeThread started. Active threads: ", threading.active_count())
    if q2.empty():
        computeThread.join()
    findingDistanceThread=threading.Thread(target=findingDistance, args=(calibration,dist,q2,q3,focal_length))
    findingDistanceThread.start()
    # print("computeThread started. Active threads: ", threading.active_count())
    ellapsedTime=time.time()-t4

    if program_terminated==True:
        if readThread.isAlive():
            readThread.join()
        if computeThread.isAlive():
            computeThread.join()
        if findingDistanceThread.isAlive():
            findingDistanceThread.join()
    print("Elapsed Time to run signalProcessingMethod is ", ellapsedTime)
    

def main():
    global all_clients_connected
    try:
        ## Server Parameters ##
        PORT = 8000
        # NUM_CAMERAS = 1        #total number of Pi/Camera's expected to connect
        imgNum=0               #counter for number of images processed 
        NUM_TRACKERS=1 

        ## Log Parameters ##
        log=True                    #enable logging
        logFName="log.txt"          #filename for log file
        #log_image_count_max = 250  #write to log once <imgNum> reaches this many images (shoud be == 4 x "circular_image_count" on Pis)

        #### Calibration Parameters ####
        dist=30 #inches
        calibration=False
        normalize=False
        
        ## Create Queues ##
        ###
        ## Make a dictionary or list of queues that has length of 3*length(addresses)
        # q1=queue.Queue() #Queue where pictures go
        # q2=queue.Queue() #Queue where cirlces go
        # q3=queue.Queue() #Queue where distances go
        ###
        queueListSize=3*len(addresses)
        queueList=[]
        for i in range(queueListSize):
            queueList.append(queue.Queue())

        ## Clear images folder ##
        folder = 'images'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)

        # ## Clear/Create log file ##
        open(logFName, 'w+')

        ## Start Server ##
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('', PORT))
        print("Server started")
        print("Waiting for clients to connect...")

        # Wait until <NUM_CAMERAS> clients connect 
        conn=0
        NUM_CAMERAS=2
        log_image_count_max = 10000
        server.listen(NUM_CAMERAS)
        clientsock, clientAddress = server.accept()
        newthread1 = ClientThread(clientAddress, clientsock)
        newthread1.start()

        ## Start all Client Threads ##
        all_clients_connected = True
        print("All clients connected!")

        # Process each image and write to log
        print("Ready for Signal Processing\n")
        while True:
            for each in range(len(addresses)):
                signalProcessingMethod("images/"+addresses[each]+str(imgNum)+".jpg",queueList[each*3],queueList[each*3+1],queueList[each*3+2],calibration,dist,focal_lengths[each])
            imgNum+=1
            if imgNum>log_image_count_max:
                normDistance(queueList,normDist)
                server.close()
                newthread1.stop()
                getLog(logFName, queueList, NUM_TRACKERS)


    except KeyboardInterrupt:
        print("\n\n**********  TERMINATING VRCADE ************\n")
        terminate_start_time=time.time()
        normDistance(queueList,normDist)
        getLog(logFName, queueList, NUM_TRACKERS)
        program_terminated=True
        server.close()
        terminate_stop_time=time.time()
        print("\nIt took %f seconds to shut down program" %(terminate_stop_time - terminate_start_time))
        print("\n**************  TERMINATED ****************\n\n\n")        
        sys.exit()


if __name__=="__main__":
    main()