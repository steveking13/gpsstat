#! /usr/bin/python
# Originally  Written by Dan Mandle http://dan.mandle.me September 2012
# Modified by Steve King
# License: GPL 2.0
 
import sys
import string
import socket
from gps import *
from time import *
import time
import threading
import getopt
 
# Constants
defaulttimeout = 300
defaulttimein = 5
defaultacceptablemode = 2
defaultsleepinterval = 2
defaulthost="localhost"

defaultreturn = 1
satsreturn=0
modereturn=0
timereturn=""

modesat = False
modetime = False

# Process command line (1: is very important)
try:
  opts,args = getopt.getopt(sys.argv[1:], "hm:o:stc:", ["help", "mode=", "timeout=", "satellites","time","host="])
except getopt.GetoptError:
  print "Command options error: try -h"
  sys.exit(2)

for opt, arg in opts:
  if opt in ("-h", "--help"):
    print '''\
gpsstat.py [options]

Utility for querying the gps status.
Unlike other utilities, gpsstat will wait for (-t timeout) seconds, and only
return if the timeout is exceeded, or the requested conditions are matched

Options:
-h --help
  This text
-m <mode> --mode=<mode>
  Mode is a numeric value where:
  0 no mode value has yet been reported (not meaningful to use)
  1 no fix
  2 Two dimensional fix (three satellites)
  3 Three dimensional fix (four or more satellites)
  when specifying this, the utility will only return when the reported
  mode is equal to or greater than that requested. Therefore a request of 4
  will not return a valid fix and will exit with 1 at the timeout
  default value: ''' + str(defaultacceptablemode) + '''
-o <seconds> --timeout=<seconds>
  Keep trying the test until the number of seconds sepcified has elapsed.
  If the conditions are not met within the time out, an error exit
  code is used.
  default value: ''' + str(defaulttimeout) + '''
-s --satellites
  Report the number of satellites being used for a fix, as the mode
  criteria is also met.
-t --time
  Report UTC time in ISO 8601 seconds/milliseconds "Z" format:
  For example: 2017-06-20T13:43:43.000Z\
-c <host> --host=<host>
  gpsd server to connect to.
'''
    sys.exit(0)
  elif opt in ("-m", "--mode"):
    defaultacceptablemode=int(arg)
  elif opt in ("-c", "--host"):
    defaulthost=arg
  elif opt in ("-o", "--timeout"):
    defaulttimeout=int(arg)
  elif opt in ("-s", "--satellites"):
    modesat=True
  elif opt in ("-t", "--time"):
    modetime=True
  else:
    print "Shouldn't get here"

gpsd = None #seting the global variable
 
class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    #gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    try :
      gpsd = gps(host=defaulthost,mode=WATCH_ENABLE) #starting the stream of info
    except socket.error:
      print "Could not connect to socket"
      sys.exit(2)

    self.current_value = None
    self.running = True #setting the thread running to true
 
  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer
 
loopcount=0
satellites=0
if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  try:
    gpsp.start() # start it up

    # We need to switch here, depending on the mode
    # We can get a gps lock before or after a list of good sats
    # So if we are waiting for sats, then we need a different end clause

    loopcontinue=True
    
    #while ( (loopcount*defaultsleepinterval) < defaulttimeout ) and (modereturn < defaultacceptablemode) :
    while ( (loopcount*defaultsleepinterval) < defaulttimeout ) and (loopcontinue) :
      print "loop"
      print gpsd.waiting()
      #It may take a second or two to get good data even if gpsd is already locked
      #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc
 
      #print
      #print ' GPS reading'
      #print '----------------------------------------'
      #print 'latitude    ' , gpsd.fix.latitude
      #print 'longitude   ' , gpsd.fix.longitude
      #print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
      #print 'altitude (m)' , gpsd.fix.altitude
      #print 'eps         ' , gpsd.fix.eps
      #print 'epx         ' , gpsd.fix.epx
      #print 'epv         ' , gpsd.fix.epv
      #print 'ept         ' , gpsd.fix.ept
      #print 'speed (m/s) ' , gpsd.fix.speed
      #print 'climb       ' , gpsd.fix.climb
      #print 'track       ' , gpsd.fix.track
      #print 'mode        ' , gpsd.fix.mode
      #print
      #print 'sats        ' , gpsd.satellites


      timereturn=gpsd.utc
      modereturn=gpsd.fix.mode  
      satsreturn = 0
      for sat in gpsd.satellites :
        if sat.used :
          satsreturn+=1

      if modesat :
        if len(gpsd.satellites) > 0 :
          loopcontinue=False
      else :
        if modereturn >= defaultacceptablemode :
	  loopcontinue=False
 
      time.sleep(defaultsleepinterval)

      loopcount+=1
 
  except (KeyboardInterrupt, SystemExit, socket.error): #when you press ctrl+c
    #print defaulttimeout
    pass
    #print "\nKilling Thread..."

gpsd.close()
gpsp.running = False
gpsp.join(4)

if modesat:
  print satsreturn

elif modetime:
  print timereturn

if modereturn >= defaultacceptablemode :
  defaultreturn=0

sys.exit(defaultreturn)
