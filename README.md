GidTech Where-U-At 2000™ Smart Home Frame
-----------------------------------------

This is a hack-job.  The code is of bad quality, but it does what I want.

It presents a web app that will track family members using their
smartphones (Life360 app; Google Location Sharing previously, but it was
unreliable); and it displays upcoming events from `ics` calendar feeds
(Google Calendar).

I have this web app running in our lobby, on a cheap Android tablet
surrounded by a cheap but nice-looking picture frame.

A previous version is described here:
https://medium.com/@gid/the-gidtech-where-u-at-2000-2ed715811977

That version used an ePaper display running on a Raspberry Pi Zero W.  The
code is in `epaperframe`, but is neglected.  I found the ePaper display
was too unreliable for use, so switched to a cheap tablet instead, running
a Kiosk web browser ( https://www.ozerov.de/fully-kiosk-browser/ )

Rather than running the calendar and location scripts on the tablet, they
run on a host computer.  Firstly, `ics` files are non-trivial to deal
with, especially with time zones and repeating events.  Fortunately,
Python has libraries to deal with them.

Secondly, Life360 doesn't seem to have a public API for this kind of
thing, but there is a rudimentary Python library which I include here --
https://github.com/harperreed/life360-python

Finally, it's possible if not likely that users will wish to display the
same information elsewhere, eg. on their own tablets or desktops, so
there's no point in checking the data multiple times.  As a result,
separating out the data collection makes it more efficient (and nicer to
Life360, among others)



[As far as licensing is concerned, I consider this roughly Apache licensed;
ie. do with it what you want, but don't stop me from using it either.]
