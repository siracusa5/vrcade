#!/usr/bin/python3

import io
import socket
import struct
import time
import threading
import picamera
import RPi.GPIO as GPIO
import time
######################################################################
### This script will connect to <address>:<port> and begin sending ###
####                photos using <threads>                         ###
######################################################################

# Camera parameters
camera_runtime = 50 #seconds
shutter_speed = 10000 #micro-seconds
framerate = 60
picture_sleep_time_duration = 0.005 #seconds
picture_sleep_time_start=0
picture_wait_time_stop=0
picture_end_time=0

image_count = 0
max_image_count= 10000
num_trackers = 1
threads=1

# Server parameters 
##address = "169.254.229.197"
address = "192.168.0.6"
port = 8000

## Connect to Server ##
# Create socket at: <address>:<port>
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Wait until connection suceeds before continuing
while True:
    try:
        client_socket.connect((address, port))
        break
    except:    
        print("Connection failed!")
        time.sleep(2)
        print("Trying again...")
        continue
print("Connected to server!")


# Create connection as file-object
# wb: write only in binary format 
connection = client_socket.makefile('wb')
try:
    #Create thread pool and locks
    connection_lock = threading.Lock()
    pool = []
    pool_lock = threading.Lock()
    #Streaming objects class
    class ImageStreamer(threading.Thread):
        def __init__(self):
            super(ImageStreamer, self).__init__()
            self.stream = io.BytesIO()
            self.event = threading.Event()
            self.terminated = False
            self.start()

        def run(self):
            global image_count, picture_end_time, picture_wait_time_start
            # This method runs in a separate background thread
            while not self.terminated:
                #Wait for image to be written to the stream
                if self.event.wait(0.01):
                    try:
                        with connection_lock:
                            print("entered image transmit block\t")
                            time_to_transmit_picture_start = time.time()
                            #Write length of capture to stream & flush buffer
                            connection.write(struct.pack('<Q', self.stream.tell()))
                            connection.write(struct.pack('<Q', image_count))
                            connection.flush()
                            #Rewind the stream & send full image
                            self.stream.seek(0)
                            connection.write(self.stream.read())
                            time_to_transmit_picture_duration = time.time()-time_to_transmit_picture_start
                            print("SENT IMAGE#: %d \tTime2Send: %f" % (image_count,time_to_transmit_picture_duration))
                            image_count += 1
                            if image_count%max_image_count==0:
                                image_count=0           
                    finally:
                        #Reset stream for next capture
                        picture_end_time=time.time()
                        self.stream.seek(0)
                        self.stream.truncate()
                        self.event.clear()
                        with pool_lock:
                            pool.append(self)

    count = 0
    start = time.time()
    finish = time.time()
    
    #Generate streams
    def streams():
        global count, finish
        global camera
        frame_count=0
        while finish - start < camera_runtime:
            # RF TX every <num_trackers> images taken
            # Get streamers from pool    
            with pool_lock:
                if len(pool) > 0:
                    streamer = pool.pop()
            yield streamer.stream
##            rfdevice.tx_code(SEND_CODE, None, PULSE_LENGTH)
            streamer.event.set()
            count += 1
            picture_wait_time_stop =time.time()
            finish = time.time()
        
        
    with picamera.PiCamera() as camera:
        pool = [ImageStreamer() for i in range(threads)]
        camera.resolution = (640, 480)
        camera.shutter_speed = shutter_speed #set shutter speed
        time.sleep(2)
        camera.start_preview() 
        camera.capture_sequence(streams(), 'jpeg', use_video_port=True)
        
        print("exposure speed: %dus\t %dfps" %(camera.exposure_speed,camera.framerate))
        
    # Shut down the streamers
    while pool:
        with pool_lock:
            streamer = pool.pop()
        streamer.terminated = True
        streamer.join()
        
except KeyboardInterrupt:
    # Shut down the streamers
    while pool:
        with pool_lock:
            streamer = pool.pop()
        print("shutting down streamer")
        streamer.terminated = True
        streamer.join()
        
finally:
    # Write the terminating 0-length to let the server know we're done
    connection.write(struct.pack('<Q', 0))
    time.sleep(1)
    connection.close()
    client_socket.close()
    rfdevice.cleanup()

## Print Final Results ##
print('Sent %d images in %.2f seconds at %.2ffps' % (
    count, finish-start, count / (finish-start)))