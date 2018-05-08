#!usr/bin/env python3
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

RECEIVE_PIN = 17
RECEIVE_CODE = 36
timestamp=0

# RF device setup
rfdevice = RFDevice(RECEIVE_PIN)
rfdevice.enable_rx()
        
# Camera parameters
camera_runtime = 50 #seconds
framerate = 60
shutter_speed = 10000 
circular_image_count = 0
max_image_count= 20000
num_trackers = 1

# Server parameters 
address = "169.254.229.197"  
port = 8000
threads = 1   #each thread is in ImageStreamer object

# Connect to pi client to <address>:<port>
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        client_socket.connect((address, port))
    except:    
        print("Connection failed...")
        time.sleep(2)
        print("Trying again")
        continue

print("Connected to server!")
# Create connection as file-object
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
            global circular_image_count
            # This method runs in a separate background thread
            while not self.terminated:
                #Wait for image to be written to the stream
                if self.event.wait(1):
                    try:
                        with connection_lock:                  
                           # Wait for RF pulse #
                           print("Waiting for RF...")
                           while True:
                               if rfdevice.rx_code_timestamp != timestamp:
                                   timestamp = rfdevice.rx_code_timestamp
                                   print("Received RF code: %d\t with Timestamp: %d" %(rfdevice.rx_code,rfdevice.rx_code_timestamp))
                                   break
                                
                                # Take <num_trackers> images, then wait for nexxt RF signal
                            frame_count=0
                            time_to_transmit_picture_start = time.time()
                              #Write length of capture to stream & flush buffer
                            connection.write(struct.pack('<Q', self.stream.tell()))
                            connection.write(struct.pack('<Q', circular_image_count))
                            print("Image#: %d\t Frame: %d" % (circular_image_count,frame_count))
                            connection.flush()
                            #Rewind the stream & send full image
                            self.stream.seek(0)
                              connection.write(self.stream.read())
                            time_to_transmit_picture_duration = time.time()-time_to_transmit_picture_start
                            print("Picture Send Duration: %f" % time_to_transmit_picture_duration)
                            circular_image_count += 1
##                          if circular_image_count%max_image_count==0:
##                             circular_image_count=0
                        frame_count += 1
                                            
                    finally:
                        #Reset stream for next capture
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
        while finish - start < camera_runtime:
            with pool_lock:
                if len(pool) > 0:
                    streamer = pool.pop()
            yield streamer.stream
            # Wait for RF pulse #
            print("Waiting for RF...")
            while True:
                if rfdevice.rx_code_timestamp != timestamp:
                    timestamp = rfdevice.rx_code_timestamp
                    ("\nReceived RF Signal at: %f\n\n" % time.time())
                    print("Received RF code: %d\t with Timestamp: %d" %(rfdevice.rx_code,rfdevice.rx_code_timestamp))
                    break
            streamer.event.set()
            count += 1       

            streamer.start()
            finish = time.time()

    with picamera.PiCamera() as camera:
        pool = [ImageStreamer() for i in range(threads)]
        camera.resolution = (640, 480)
        shutter_speed = 10000 
        #Start preview & let camera warm up
        camera.shutter_speed = shutter_speed #set shutter speed
##        camera.start_preview()
        time.sleep(2)
        camera.capture_sequence(streams(), 'jpeg', use_video_port=True)
           
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
        streamer.terminated = True
        streamer.join()
finally:
    # Write the terminating 0-length to let the server know we're done
    connection.write(struct.pack('<Q', 0))
    time.sleep(2)
    connection.close()
    client_socket.close()
    rfdevice.cleanup()


print('Sent %d images in %.2f seconds at %.2ffps' % (
    count, finish-start, count / (finish-start)))