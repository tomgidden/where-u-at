#!/usr/bin/env python3


debug = False

mqtt_host = 'mqtt.home'
import paho.mqtt.client as paho

from calzone import Calzone

from icalendar import Calendar, Event
from pytz import timezone
import datetime
import email.utils
import calendar
import time

import concurrent.futures
import requests
from requests_futures.sessions import FuturesSession

from cachecontrol import CacheControlAdapter
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import ExpiresAfter

import os
import sys

import json

localtz = timezone('Europe/London')
oneday = datetime.timedelta(hours=24)
now = localtz.localize(datetime.datetime.now())
midnight = localtz.localize(datetime.datetime.combine(now, datetime.time(0,0,0)))

from cachecontrol.heuristics import BaseHeuristic
class ForceCacheHeuristic(BaseHeuristic):
    def update_headers(self, response):
        expires = now + datetime.timedelta(minutes=15)
        txt = email.utils.formatdate(calendar.timegm(expires.timetuple()))
        return {
            'expires' : txt,
            'cache-control' : 'public',
        }

calendars = {
    'cal1': 'https://calendar.google.com/calendar/ical/example%40gmail.com/private-1234/basic.ics'
}

def on_disconnect(mqtt, userdata, rc):
    print("Disconnected from MQTT server with code: {}".format(rc))
    while rc != 0:
        try:
            time.sleep(1)
            rc = mqtt.reconnect()
        except:
            pass
        print("Reconnected to MQTT server.")

mqtt = paho.Client()
mqtt.connect(mqtt_host, 1883, 60)
mqtt.on_disconnect = on_disconnect
mqtt.loop_start()


def get_events_from_icalendars():
    global now, midnight

    now = localtz.localize(datetime.datetime.now())
    midnight = localtz.localize(datetime.datetime.combine(now, datetime.time(0,0,0)))

    cz = Calzone()

    session = FuturesSession()
    session.mount('https://', CacheControlAdapter(cache=FileCache('.webcache'), heuristic=ForceCacheHeuristic()))

    cals = {k: session.get(u) for k,u in calendars.items()}

    concurrent.futures.wait(cals.values())

    for k,req in cals.items():
        try:
            cz.load(req.result().text)
        except Exception as err:
            print("Failed to load calendar '{}'".format(k))
            print (err)

    try:
        events = cz.get_events(midnight, midnight + datetime.timedelta(days=90))
    except Exception as e:
        print (e)

    events.sort(key=lambda e: e.start)

    return events


calendar_topic = "/calendar"

j = None
try:
    while True:
        try:
            while True:
                oj = j
                es = get_events_from_icalendars()
                j = '['+(','.join([str(e) for e in es]))+']'

                if j == oj:
                    time.sleep(3600)
                else:
                    print("Publishing...")
                    print(j)
                    if not debug:
                        mqtt.publish(calendar_topic + "/all_events", j, retain=True)
                        mqtt.publish(calendar_topic + "/all_events/updated", int(time.time()), retain=True)
                    time.sleep(60)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print("LOOP EXCEPTION")
            raise e
            print(e)
            time.sleep(3)
except KeyboardInterrupt:
    pass
