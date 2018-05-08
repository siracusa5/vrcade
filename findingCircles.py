import cv2
import numpy as np
import time
import threading
import queue


def readFile(fName,q):
    """ Reads in an expected file and returns it. If no image is found 
    then it is called again until that file is found """
    t0=time.time()
    print ("Trying to read from", fName)
    try: 
        img=cv2.imread(fName,cv2.IMREAD_COLOR)
        #cimg=cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
        assert(img is not None)
        q.put(img)
        print("Image Read")
    except:
        print("No", fName, "found yet. Checking again.")
        time.sleep(1)
        img=readFile(fName,q)
    #print("Time required to read the file,", time.time()-t0)

def callCanny(img, highThresh, lowThresh):
    """Calls the Canny algorithm which creates a contour of the original photo that 
    can then be used by houghLines algorithm"""
    contours = cv2.Canny(img,highThresh,lowThresh,apertureSize = 3)
    #################################################
    # shows edges image for debugging purposes
    #cv2.imshow('canny Edges',contours)
    #cv2.waitKey(0)
    return (contours)

def callHoughCircles(contours,img,highThresh,lowThresh, accumulatorThresh,count):
    """ Calls the hough circle transform. Canny function must be called beforehand and passed as the
   parameter. Returns the (x,y, radius) 
   NOTE: param1 should equal the larger of the two parameters in cv2.Canny"""
    count=count+1
    circles = cv2.HoughCircles(contours,cv2.HOUGH_GRADIENT,1,10,
                           param1=highThresh,param2=accumulatorThresh,minRadius=2,maxRadius=8)
        # if count is 1:
        #     print("No circles were found, trying at a lower accumulatorThreshold.")
        #     contours=callCanny(img, highThresh/2, lowThresh*2)
        #     circles=callHoughCircles(contours,img,highThresh/2,lowThresh*2, accumulatorThresh/2)
        # print("No circles found after 2 tries, confident saying there are no circles.")
    #print(circles)
    return (circles)

def drawCircles(circles, cimg):
    """For debugging purposes, to visually see what circles it is finding"""
    circles = np.uint16(np.around(circles))
    for i in circles[0,:]:
        print (i)
         #draw the outer circle
        cv2.circle(cimg,(i[0],i[1]),i[2],(0,255,0),1)
         #draw the center of the circle
        cv2.circle(cimg,(i[0],i[1]),2,(0,0,255),1)

    cv2.imshow('detected circles',cimg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def compute(q1,q2,highThresh,lowThresh, accumulatorThresh,count):
    """Finds all the circles in the input queue, q1, and outputs the 
   (x,y,radius) of the cirlces to a np array. If anything other than 3 or
   4 circles are found, the np array is an array of 0's"""
    t1=time.time()
    img=q1.get()
    contours=callCanny(img,highThresh,lowThresh)
    ## Testing contours
    #callFindContours(contours)
    ##
    circles=callHoughCircles(contours,img,highThresh,lowThresh,accumulatorThresh,count)
    ## Make sure we have the right number of cirlces, else make it a 0 (4X3) array
    if circles is None:
        del (circles)
        circles=[np.zeros((4,3))]
    if len(circles[0])<3 or len(circles[0])>4:
        #print("Circles[0] are", circles[0])
        del (circles)
        circles=[np.zeros((4,3))]
        #print("Circles[0] are", circles[0])
        ###########It is full of nan values so need to figure out how to determine that
    q2.put(circles)
    deltaT=time.time()-t1
    #print("Time Ellapsed to compute Hough transform was", deltaT)
    #drawCircles(circles,img)

        

if __name__=="__main__":
    fileName="25inches.jpg"
    q1=queue.Queue()
    q2=queue.Queue()
    signalProcessingMethod(fileName,q1,q2)

