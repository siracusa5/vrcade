import numpy as np
import queue
import math
#from findingCircles import signalProcessingMethod


def getPixWidth(circles):
    """Subtracts the y1 and y2 values with the least amount of skew.
    It also destroys the circle array"""
    minXsep=100
    yCoordSep=0
    for x in range(len(circles)):
        if x < len(circles):
            circle=circles[x-1]
            #print("circle is", circle)
            circles=np.delete(circles,x-1,0)
           # print("New circles", circles)
        else:
            circle=circles[0]

        for each in circles:
            #print(circle[1])
            xCoordSep=np.absolute(circle[0]-each[0])
            if xCoordSep<minXsep:
                if np.absolute(circle[1]-each[1])>0.001:
                    yCoordSep=np.absolute(circle[1]-each[1])
                minXsep=xCoordSep
        return(yCoordSep)

def getFocalLength(dist, width, pixWidth):
    """ Calibration function that should only happen once.
    Have the tracker at a known distance and find the pix Width
    to find the relative focal length that is used in determining 
    distance in other cases."""
    focalLength=(pixWidth*dist)/width
    return(focalLength)

def getDistance(trueWidth,focalLength,pixWidth):
    """Finds the distance from the camera to the object
    using triangle simularity"""
    distance=(trueWidth*focalLength)/pixWidth
    print("Distance is",distance)
    return distance

def getCartCoords(circles,distance,pixWidth,cameraRes=[640,480], FOV=70*math.pi/180, trackerHeight=2.392,):
    """Normalize and average all the x and y coordinates to the middle
    of the cameras screen. Then find the angle that the image is offset so that
    we have a radial position of (distance,angle)."""
    xCoords=[]
    yCoords=[]
    for each in range(len(circles)):
        if each < len(circles):
            circle=circles[each-1]
            #print("circle is", circle)
            circles=np.delete(circles,each-1,0)
           # print("New circles", circles)
        else:
            circle=circles[0]
        xCoords.append(circle[0])
        yCoords.append(circle[1])
    
    xMidPt=cameraRes[0]/2
    yMidPt=cameraRes[1]/2
    ##### Normalize coordinate grid to the center of the screen ####
    xCoordsNorm=np.subtract(xCoords,xMidPt)
    yCoordsNorm=np.subtract(yCoords,yMidPt)
    ##### Avg x and y coordinates ####
    xCoordAvg=0
    for each in xCoordsNorm:
        xCoordAvg+=each
    xCoordAvg=xCoordAvg/len(xCoordsNorm)
    yCoordAvg=0
    for each in yCoordsNorm:
        yCoordAvg+=each
    yCoordAvg=yCoordAvg/len(yCoordsNorm)
    #### Find x, y, z distance ####
    x=xCoordAvg/pixWidth*trackerHeight
    y=yCoordAvg/pixWidth*trackerHeight
    
    
    #xFOV=distance*np.tan(FOV)
    #yFOV=xFOV
    #x=xCoordAvg/(cameraRes[0]/2)*xFOV
    #y=yCoordAvg/(cameraRes[1]/2)*yFOV
    z=np.sqrt(distance**2-x**2-y**2)
    return([x,y,z])


if __name__=="__main__":
    """Just random numbers as of now, circles will be received from 
    earlier code and will also be used to find pixWidth"""
    calibration=False
    q1=queue.Queue()
    q2=queue.Queue()
    #Calibration
    dist=25 #inches
    trueWidth=3.005 #inches
    #
    signalProcessingMethod("30inches.jpg",q1,q2)
    circles=q2.get()[0]
    print("circles are, ", circles)
    pixWidth=getPixWidth(circles)
    if calibration:
        focalLength=getFocalLength(dist,trueWidth,pixWidth)
        print("Calibrated Focal Lenght is", focalLength)
    else:
        focalLength=1272
        distance=getDistance(trueWidth,focalLength,pixWidth)
        print("Determined distance from camera is", distance)
        #angle=getAngle(circles[0],circle[1],cameraRes)

