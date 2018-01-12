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

1. Recompile ntpd to support PPS.
2. Reconfigure the Rasperry PI to provide /dev/ttyAMA0 (GPIO serial port)
3. Configure gpsd to use /dev/ttyAMA0
4. Configure ntpd to use gpsd as an artifically high stratum time source
5. Change /etc/init.d/ntp so that it runs this script to ensure that the GPS has locked before it tries to use the /dev/ttyAMA0 time data.
6. A cronjob that ensures that the time sync is using the PPS time signal (bit of a hack)

The basis for this was a fairly old article here:
http://www.satsignal.eu/ntp/Raspberry-Pi-NTP.html
which details the ntpd changes, but is based on obsolete hardware (raspberry pi 1)
My hardware is also out of date, but follow the link on that article for a PPS/GPS module that will work with more recent pi models.

As far as I know, the current module will work with this script.

More detail to follow.
