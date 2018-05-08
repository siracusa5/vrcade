import threading
import io
import socket
import struct
import time
from PIL import Image

class ClientThread(threading.Thread):

    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        print ("New connection added: ", clientAddress)
        
    def run(self):
        # print ("Connection opened: ", clientAddress)
        count=0
        imageNum=1
        connection = self.csocket.makefile('rb')
        while True:
            # Receive size of each image
            size = struct.unpack('<Q',connection.read(struct.calcsize('<Q')))[0]
            # Break loop when client sends 0-length byte
            if size==0:
                print('Received %d images from %s' % (count,(clientAddress[0])))
                break  
            # Put image data into byte stream, open & save to file
            imageNum = struct.unpack('<Q',connection.read(struct.calcsize('<Q')))[0]
            print("imageNum: %d\tImageSize: %d" % (imageNum,size))
            image_stream = io.BytesIO()
            image_stream.write(connection.read(size))
            image_stream.seek(0)
            # try:
            image = Image.open(image_stream)
            image.save('images/%s__%d.jpg' % ((clientAddress[0]),imageNum))
            count += 1
            # except IOError:
                # pass
            
        print ("Client ", clientAddress , " disconnected...")
        self.csocket.close()
        server.close()
        print("Socket closed")

def getImgStreams():
    PORT = 8000
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ##server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
    server.bind(('', PORT))
    print("Server started")
    print("Waiting for client request..")
    while True:
        server.listen(5)
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.start()

# if __name__=="__main__":
#     getImgStreams()
