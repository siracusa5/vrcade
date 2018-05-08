import numpy as np
import queue 

def normDistance(queueList, normDistList):
    """Takes in x and y coord based queue lists and normalize the
    distances to the first camera"""
    for count in range(int(len(queueList)/3)):
        adjustedCount=count+1
        newX=[]
        newY=[]
        newZ=[]
        xyzQueue=queueList[adjustedCount*3-1]
        for each in range(int(xyzQueue.qsize()/3)):
            x=xyzQueue.get()
            y=xyzQueue.get()
            z=xyzQueue.get()
            newX.append(x-normDistList[count*2])
            newY.append(y-normDistList[count*2+1])
            newZ.append(z-normDistList[count*2+2])
        for each in range(len(newX)):
            xyzQueue.put(newX[each])
            xyzQueue.put(newY[each])
            xyzQueue.put(newZ[each])


if __name__=="__main__":
    normDist()
