#!/usr/bin/python3

import io
import socket
import struct
import time
import threading
import picamera
import RPi.GPIO as GPIO
import time
from rpi_rf import RFDevice
######################################################################
### This script will connect to <address>:<port> and begin sending ###
####                photos using <threads>                         ###
######################################################################

# RF parameters
SEND_PIN = 17  #GPIO pin number
SEND_CODE = 36
PULSE_LENGTH = 200  #milliseconds
##RF_pulse_duration = 0.330

# Camera parameters
camera_runtime = 20 #seconds
shutter_speed = 5000 #micro-seconds
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
address = "169.254.229.197"  
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
        time.sleep(5)
        print("Trying again...")
        continue
print("Connected to server!")

# RF device setup
rfdevice = RFDevice(SEND_PIN)
rfdevice.enable_tx()

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
                        print("Time from beginning of RF to end of image capture %f" %(picture_end_time-picture_wait_time_start))
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
        RF_pulse_duration=0.340
        global count, finish, picture_end_time, picture_wait_time_start
        global camera
        frame_count=0
        while finish - start < camera_runtime:
            # RF TX every <num_trackers> images taken
            print("frame: %d " %frame_count)
            
            # Get streamers from pool    
            with pool_lock:
                if len(pool) > 0:
                    streamer = pool.pop()
            yield streamer.stream
            streamer.event.set()
            
            if frame_count == 0:
                RF_pulse_time_start = time.time()
                print("RF Puclse sent at: %f" %time.time())
                rfdevice.tx_code(SEND_CODE, 1, PULSE_LENGTH)
                print("Actual RF Pulse Duration: %f" %(time.time()-RF_pulse_time_start))
                # Wait for full Pulse duration
                time.sleep(RF_pulse_duration - (time.time()-RF_pulse_time_start))
                print("Delayed RF Pulse Execute Time: %f" %(time.time()-RF_pulse_time_start))
               picture_wait_time_start= time.time()
               frame_count += 1
           elif frame_count > (num_trackers-1):
               frame_count = 0
                time.sleep(picture_sleep_time_duration - (time.time() - picture_wait_time_start))
           else:
               frame_count += 1
               time.sleep(picture_sleep_time_duration - (time.time() - picture_wait_time_start))
        
            count += 1
            picture_wait_time_stop =time.time()
##            print("From beginnning of pulse to End of image capture_time: %f" %(picture_wait_time_stop-picture_wait_time_start))
            finish = time.time()
        
        
    with picamera.PiCamera() as camera:
        pool = [ImageStreamer() for i in range(threads)]
        camera.resolution = (640, 480)
##        camera.framerate = framerate
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
    rfdevice.cleanup()
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
    time.sleep(2)
    connection.close()
    client_socket.close()
    rfdevice.cleanup()

## Print Final Results ##
print('Sent %d images in %.2f seconds at %.2ffps' % (
    count, finish-start, count / (finish-start)))