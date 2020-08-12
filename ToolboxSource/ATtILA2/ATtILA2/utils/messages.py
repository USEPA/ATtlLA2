'''
This module contains tools for sending status messages to the command line and the ArcGIS GeoProcessor
'''
import arcpy
import datetime

def AddMsg(msg, severity=0):
    # Adds a Message (in case this is run as a tool)
    # and also prints the message to the screen (standard output)
    # 
    #print msg

    # Split the message on \n first, so that if it's multiple lines, 
    #  a GPMessage will be added for each line
    try:
        for string in msg.split('\n'):
            # Add appropriate geoprocessing message 
            #
            if severity == 0:
                arcpy.AddMessage(string)
            elif severity == 1:
                arcpy.AddWarning(string)
            elif severity == 2:
                arcpy.AddError(string)
    except:
        pass
    
class loopProgress:
    count = 0
    def __init__(self, total):
        self.total = total
        self.startTime = datetime.datetime.now()
        self.increment = int(total/10.0)
        if self.increment == 0: # handle case where total is less than five and the int function rounds down to zero
            self.increment = 1 # avoid divide-by-zero error by setting equal to 1.
    
    def update(self):
        self.count += 1
        if (self.count % self.increment) == 0:
            pctComplete = str(100 * self.count / self.total)
            elapsed = datetime.datetime.now() - self.startTime
            estRemaining = self.timeToStr(elapsed.seconds * self.total / self.count - elapsed.seconds)
            avgLoop = self.timeToStr(elapsed.seconds / self.count)
            elapsedStr = self.timeToStr(elapsed.seconds)
            message = "{0} out of {1} loops, {2}% complete, {3} elapsed, est. {4} remaining, average time per loop: {5}"
            AddMsg(message.format(self.count,self.total,pctComplete,elapsedStr,estRemaining,avgLoop))

    def timeToStr(self,secs):
        return str(datetime.timedelta(seconds=secs)).split('.')[0]