import multiprocessing
import socket
import io
import struct
import time
from PIL import Image

def handle(connection, address):
        try:
            count=0
            conn = connection.makefile('rb')
            while True:
                # Receive size of each image
                size = struct.unpack('<Q',conn.read(struct.calcsize('<Q')))[0]
                # print("ImgCount: %d\tImageSize: %d" % (count+1,size))
                # Break loop when client sends 0-length byte
                if size==0:
                    print('Received %d images from %s' % (count, address))
                    break  
##                print("Image Size: %d" %(intSize))
                # Put image data into byte stream, open, & save to file
                image_stream = io.BytesIO()
                image_stream.write(conn.read(size))
                image_stream.seek(0)
                # try:
                image = Image.open(image_stream)
                image.save('images/%s__%d.jpg' % ((address[0]),count))
                count += 1
                # except IOError:
                    # pass
        finally:
            print("Closing socket: %s" % (address[0]))
            connection.close()

class Server(object):
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.socket.setblocking(0)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(5)

        while True:
            conn, address = self.socket.accept()
            print('Accepted connection!')
            process = multiprocessing.Process(target=handle, args=(conn, address))
            process.daemon = True
            process.start()

    def close(self):
        self.socket.close()
            
            
if __name__ == "__main__":
    server = Server('', 8000)
    try:
        server.start()
    except:
        print("Unexpected exception")
        for process in multiprocessing.active_children():
            process.terminate()
            process.join()
