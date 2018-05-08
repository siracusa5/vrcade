import queue
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plot

def getLog(fName, queueList,numTrackers=1):
    try:
        numTrackersList=[]
        for each in range(0,numTrackers):
            numTrackersList.append([])
            numTrackersList.append([])
            numTrackersList.append([])

        with open(fName, 'a+') as f:
            print("Writing log file: %s" %fName)
            print(" queueList: ", range(len(queueList)))
            for count in range(int(len(queueList)/3)):
                queueCount=(count+1)*3-1
                print (" queueCount: %d" %queueCount)
                logQueue=queueList[queueCount]
                print (" logQueue Size: %d" %logQueue.qsize())
                xList=[]
                yList=[]
                zList=[]
                tracker=0
                for each in range(int(logQueue.qsize()/3)):
                    x=logQueue.get()
                    y=logQueue.get()
                    z=logQueue.get()
                    f.write("The distance away from the camera for photo "+str(each)+" is ("+str(x)+","+str(y)+","+str(z)+")")
                    f.write("\n")
                    xList=numTrackersList[(tracker)*3]
                    yList=numTrackersList[(tracker)*3+1]
                    zList=numTrackersList[(tracker)*3+2]
                    xList.append(x)
                    yList.append(y)
                    zList.append(z)
                    tracker+=1
                    if(tracker>=numTrackers):
                        tracker=0

            fig = plot.figure()
            ax = fig.add_subplot(111,projection='3d')
            ax.scatter(xList,zList,yList,c='b')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_xlim([-80,80])
            ax.set_ylim([0,140])
            ax.set_zlim([-48,48])
            plot.show()

            plot.close()


    except KeyboardInterrupt:
        plot.close()
        return

if __name__=="__main__":
    main()
