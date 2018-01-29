# gpsstat
monitor gpsd, return when a lock is established.

Introduction

I have a raspberry pi with GPS/PPS module.
After a power outage, the pi's time keeping would often be confused.
PPS only provides a signal for the seconds, it doesn't set the clock absolutely.

If it came up with no network, it would have an error ~= the duration of the power outage.

If that outage was > 3000 seconds, ntpd would fail to ever resynchronise.

However, the GPS module I had for the PPS, with a bit of tweaking, would deliver NMEA data to the GPIO virtual serial port. Surely that was the answer?

But is there any utility that can tell you if the GPS has a lock? I couldnt find one. gpsd relies on the client to identify the state of the lock.

So, I this (gpsstat) sits listening to gpsd until it gets a lock symbol.

Configuration

This uses the gps python module (which is included with recent gpsd)

In order to configure the desired behaviour for my raspberry pi, this is only part of the story.

1. Reconfigure the PI to support PPS over GPIO
2. Reconfigure the PI to provide /dev/ttyAMA0 (GPIO serial port)
3. Recompile ntpd to support PPS.
4. Configure gpsd to use /dev/ttyAMA0
5. Configure ntpd to use gpsd as an artifically high stratum time source
6. Change /etc/init.d/ntp so that it runs this script to ensure that the GPS has locked before it tries to use the /dev/ttyAMA0 time data.
7. A cronjob that ensures that the time sync is using the PPS time signal (bit of a hack)

The basis for this was a fairly old article here:
http://www.satsignal.eu/ntp/Raspberry-Pi-NTP.html
which details the ntpd changes, but is based on obsolete hardware (raspberry pi 1)
My hardware is also out of date, but follow the link on that article for a PPS/GPS module that will work with more recent pi models.

As far as I know, the current module will work with this script.

More detail to follow.

1. Reconfigure the PI to support PPS over GPIO
Add these lines to /boot/config.txt
# pps GPIO pin
dtoverlay=pps-gpio,gpiopin=18

Ensure that the gpiopin parameter matches that in your GPS card documentation

Then add this to /etc/modules
pps-gpio

Reboot the PI (or wait until you have done the step 2)

To verify that this is working:
apt-get install pps-tools
ppstest /dev/pps0

source 0 - assert 1516102326.992172280, sequence: 8108815 - clear  0.000000000, sequence: 0
source 0 - assert 1516102327.992168777, sequence: 8108816 - clear  0.000000000, sequence: 0
source 0 - assert 1516102328.992167319, sequence: 8108817 - clear  0.000000000, sequence: 0

(Be aware that configuring ttyAMA0, step 2, will create a /dev/pps1 which is of no use to us)


2. Reconfigure th PI to provide /dev/ttyAMA0
Add these lines to /boot/config.txt

# /dev/ttyAMA0
enable_uart=1

To verify this is working, before you enable gpsd,
By default the GPS module will use NMEA packets, so you should see: 
(The data have been annonymised)

sudo cat -v /dev/ttyAMA0
$GPRMC,113847.00,A,xxxx.07472,x,xxxxx.39012,x,0.334,,160118,,,A*31^M
$GPVTG,,T,,M,0.334,N,0.618,K,A*28^M
$GPGGA,113847.00,xxxx.07472,x,xxxx.39012,x,1,09,0.95,31.3,M,16.6,M,,*63^M
$GPGSA,A,3,13,xx,xx,xx,xx,xx,xx,xx,xx,xx,,,1.51,0.95,1.18*17^M
$GPRMC,113848.00,A,xxxx.07457,x,xxxxx.39005,x,0.385,,160118,,,A*15^M
$GPVTG,,T,,M,0.385,N,0.714,K,A*2F^M
$GPGGA,113848.00,xxxx.07457,x,xxxxx.39005,x,1,09,0.95,61.5,M,46.6,M,,*5B^M
$GPGSA,A,3,12,xx,xx,xx,xx,xx,xx,xx,,,,,1.51,0.95,1.18*27^M
$GPRMC,113849.00,A,xxxx.07459,x,xxxxx.39006,x,0.231,,160118,,,A*37^M
$GPVTG,,T,,M,0.231,N,0.428,K,A*2D^M
$GPGGA,113849.00,xxxx.07459,x,xxxxx.39006,x,1,09,0.95,61.5,M,46.6,M,,*79^M
...

gpsd is able to control the gps receiver, and may switch the gps data into binary format.

Then reboot the PI

3. Recompile ntpd to support PPS.
On a raspian, the standard NTP doesn't have PPS support compiled in. It is therefore necessary to compile your own local version. On raspian, and other debian like systems, you can quite easily download the sources, and recompile the package yourself.

mkdir tmp
cd tmp
apt-get source ntp
[sudo] apt-get build-dep ntp
[sudo] apt-get install devscripts

cd ntp-4.<version>

Edit the file in the source debian/rules, to add an extra option to the configure script: Add the line with the "+" at the beginning

@@ -23,6 +23,7 @@
                --disable-local-libopts \
                --enable-ntp-signd \
                --disable-dependency-tracking \
+                --enable-linuxcaps \
                --with-openssl-libdir=/usr/lib/$(DEB_HOST_MULTIARCH)


Then run dch
This bumps the version of the package up, so that apt won't automatically undo your changes.

Add an entry like this:
ntp (1:4.2.6.p5+dfsg-7+deb8u2.1) UNRELEASED; urgency=medium

  * Non-maintainer upload.
  * Added support for PPS

 --  <pi@raspberrypi>  Tue, 16 Jan 2018 14:06:08 +0000

Save the file, then run dch again:
dch -r
This second step marks the package for release
Then build the package:

debuild

this will take a while, especially on a single core pi. The "fatal" error at the end, is down to you not being the package maintainer, not having the gpg private key.

Install your custom package:
cd ..
[sudo] dpkg -i ntp_4.<version>_armhf.deb

If a bugfixed version is released, you will have to repeat the process with the newer version of the package, otherwise apt will overwrite your custom package with a newer version.

Check that ntpd is working, by running:
ntpq -p



4. Configure gpsd to use /dev/ttyAMA0

apt-get install gpsd python-gps

edit /etc/default/gpsd
and add the serial device of the GPIO serial port to the "DEVICES" setting:

DEVICES="/dev/ttyAMA0"

restart the gpsd

service gpsd restart

Check that the gps has found your GPS device, and that it is correctly placed to grab a lock.

cgps

(gpsd uses its own protocol to report GPS data)

{"class":"TPV","tag":"0x0106","device":"/dev/ttyAMA0","mode":3,"time":"2018-01-16T15:02:39.000Z","ept":0.005,"lat":xx.xx1302711,"lon":x.xx3236587,"alt":68.183,"epx":59.419,"epy":18.710,"epv":40.940,"track":45.4071,"speed":0.014,"climb":-0. 020,"eps":0.37,"epc":81.88}


5. Configure ntpd

We add two time sources to ntp.conf:
a) The PPS source
b) The local GPS

It is possible to run the time service purely with the GPS and PPS sources, however, unless your environment prevents this, I would always recommend adding a number of additional sources. The beauty of NTP is that it picks the best, so you are not making your clock less accurate by adding more sources.

Selecting good quality, additional low-latency time sources.

In order to tune and verify the accuracy of your own clock, it is worth spending some time on identifying other reliable ntp servers. Even if you don't plan on making your ntp service publicly available.

The default ntp configuration of raspian provides a set of pool.ntp.org servers to act as reference. (See http://www.pool.ntp.org)

These round-robbin with a database of time servers of varying quality.

I recommend monitoring the output fron ntpq -p, identifying a reliable source (one with a * (or + ) in the left-hand column, restarting ntpd, and then checking again after a few hours. Restarting the daemon refreshes the ntp servers, so you should get a new set.

If you do this a few times, you should have a set of reasonable sources. Of course, you can never guarantee that the server won't be taken down, or hobbled in some other way.

Alternatively, if your ISP provides an ntp server that you can access, and it seems good enough, it probably has a low latency.

This is an on-going process. It is always worth checkin in on your preferred servers to see if some of the have gone away, or just aren't accurate any more.

The problems I have seen with servers are:
 losing it's own time sources and drifting.
 losing it's DNS entry
 just going away
 failing to account for leap seconds

The second column of the output from ntpq -p shows the remote clock's reference ID.
This is often another ntp server, but certain sources can be based on clock hardware. https://tools.ietf.org/rfc/rfc5905.txt

You need to add the PPS and GPS clock sources to your ntp.conf file.

# PPS
server 127.127.22.0 minpoll 4 maxpoll 4
fudge 127.127.22.0 time1 -0.008 flag3 1 refid PPS

# GPS
server 127.127.28.0 minpoll 4 maxpoll 4
fudge 127.127.28.0 time1 0.101 refid GPS stratum 9

To explain the above:
The IP addresses aren't realy used as IP addresses, both identify the local host, (which is 127.0.0.0/8), but the particular addresses the type of time source.

minpoll/maxpoll are the minimum and maximum time between probes though the value is not in seconds. It is (two raised to the power of the specified value) seconds. The value "4" is equivalent to sixteen seconds.

The time1 option specifies a time to add to the output of the reference clock in seconds. This deals with propagation delays and similar small adjustments ascosiated with precision time keeping. The only way to establish an appropriate value for this is by comparing the time of your reference clock with other well calibrated time sources. It may well take some time to get a good value. Keep a record of what previous values were, and don't be afraid to tinker. If other time sources are -ve offset compared to your reference, you should reduce this value by the appropriate amount. Remember the offset is reported in milliseconds.
I have found that a GPS receiver, over an emulated serial port on a USB device can fluctuate +-8 milliseconds, so consider the average over at least an hour beforem making an adjustment.
The PPS receiver fluctuation is much, much smaller, of the order of 2 microseconds, but still needs care to set. Due to network inconsistincies, ntp servers on the internet will fluctuate.

flagl 1 enables the linux kernel PPS discipline. Makes the kernel aware of the PPS source.

The refid option provides the label for the reference ID when reporting the clock source. The default value isn't very descriptive.

The stratum option overrides the default stratum. In this case, the GPS source would default to stratum zero - ntp would then prefer the GPS source compared to the PPS source, and because the GPS source is delivered via a 4800 baud serial port, it has considerably more jitter than the PPS. So we force it to use PPS by downgrading GPS.

6. Change /etc/init.d/ntp so that it runs this script to ensure that the GPS has locked before it tries to use the /dev/ttyAMA0 time data.

Add "gpsd" to the list of required start parameters.
# Required-Start:  $network $remote_fs $syslog gpsd

(Note to self, there is probably a proper systemd way to do this)

Add the following lines (those starting with +):

@@ -54,6 +54,24 @@
 case $1 in
        start)
                log_daemon_msg "Starting NTP server" "ntpd"
+                # Modify the start to wait for gpsd to get a lock
+                # then set the local time to that provided by GPS
+
+                if test -x /usr/local/bin/gpsstat && ! /usr/local/bin/gpsstat
+                then
+                        logger -p info -i -t ntpd "Timed out GPS"
+                else
+
+                        gpstime=$(date -u --date=$(/usr/local/bin/gpsstat -t) +%s)
+                        systime=$(date -u +%s)
+                        if [ "$(( $gpstime - $systime ))" -gt 1000 ]
+                        then
+                               logger -p info -i -t ntpd "System time too slow: $(date -u) setting to gpstime"
+                               log_daemon_msg "Setting sysclock to gps clock" "ntpd"
+                               date -u $( date -u --date=$(/usr/local/bin/gpsstat -t) +%m%d%H%M%Y.%S )
+                               logger -p info -i -t ntpd "System time now: $(date -u)"
+                        fi
+                fi
 
                if [ -z "$UGID" ]; then
                        log_failure_msg "user \"$RUNASUSER\" does not exist"

This block does two extra things:
1. it uses gpsstat to wait for a gps lock
2. it uses a gps reported time to set the local clock.

It only does and absolute set if the gpstime differs from the local clock by more than 1000 seconds. ntpd will reset the clock when it starts, if the differnce is smaller than 3000 seconds.

These changes rely on the gpsstat script being installed in /usr/local/bin/
If it is somewhere else, you need to modify the changes.

I would recommend uninstalling the ntpdate package, which is kind of depracated by the ntp people anyway. ntpdate uses /etc/ntp.conf to locate a time server, and do a one-off sync.

If the internet is down, this will fail after a timeout. Our changes are a superior setting anyhow.

After editing it, to keep systemd happy:
systemctl daemon-reload


7. A cronjob that ensures that the time sync is using the PPS time signal (bit of a hack)

The final hack, and this is a bit of hack, is a cronjob that checks the ntp discipline, and if it isn't PPS, it restarts the ntp service.

I found, that even with all the changes already done, sometimes ntp would fail to poll the PPS service. The reach would never change, suggesting that ntpd wasn't using the PPS at all.

So if this script finds that the reach is zero for the PPS source, it restarts ntpd

#!/bin/bash

PATH=/usr/local/bin:/usr/bin:/bin

# Only intervene if the system has been up for a while
if [ "$( cut -f 1 -d'.' /proc/uptime )" -lt "1000"  ]
then
  exit 0
fi

# If the ntp service hasn't latched on to the PPS, restart it.
if ntpq -p |egrep '^ PPS\(0\) *[.]PPS[.] *0 *l *- *[[:digit:]]+ *0' > /dev/null
then
  /usr/sbin/service ntp restart
fi

This is installed in /usr/local/sbin/checkPPS and the following line is added to root's crontab:

1/31 * * * *         /usr/local/sbin/checkPPS

