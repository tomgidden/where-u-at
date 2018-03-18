#!/usr/bin/env python3

debug = False

mqtt_host = 'mqtt.home'
import paho.mqtt.client as paho

import geopy.geocoders.base
geopy.geocoders.base.DEFAULT_USER_AGENT = 'GidTech-Where-U-At/0.1'
import urllib.request
urllib.request.OpenerDirector.client_version = 'GidTech-Where-U-At/0.1'

from life360 import life360
import math
import time
import os
import sys
import datetime
import re
from geopy.geocoders import GoogleV3

geolocator = GoogleV3(api_key="XXXX", user_agent="GidTech-Where-U-At/0.1")

import json

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

# Life360 auth token
authorization_token = "XXXX"

# Life 360 login
username = "xxxx@xxx.net"
password = "xxxx"

people = {}
locations = {
    "HOME": { 'latitude': 51.0000, 'longitude': -2.0000, 'radius': 40 },
    "The Mall": { 'latitude': 51.5251277, 'longitude': -2.5972443, 'radius': 200 },
    "Vue Cribbs Causeway": { 'latitude': 51.523171, 'longitude': -2.6059989, 'radius': 100 },
    "Southmead Hospital": { 'latitude': 51.4950162, 'longitude': -2.5918747, 'radius': 200 },
    "Clevedon Hospital": { 'latitude': 51.4376361, 'longitude': -2.8473435, 'radius': 200 }
}

def distance_between(lat, lon, hlat, hlon):
    theta = hlon - lon
    dist = math.sin(lat*3.1415927/180.0) * math.sin(hlat*3.1415927/180.0) + math.cos(lat*3.1415927/180.0) * math.cos(hlat*3.1415927/180.0) * math.cos(theta*3.1415927/180.0);
    dist = math.acos(dist);
    dist = dist*180.0/3.1415927
    return dist * 60 *  1853;


def get_updates():
    api = life360(authorization_token=authorization_token, username=username, password=password)
    if api.authenticate():
        circles =  api.get_circles()
        for circle_info in circles:
            id = circle_info['id']
            circle = api.get_circle(id)

            for m in circle['members']:

                lat = float(m['location']['latitude'])
                lon = float(m['location']['longitude'])
                acc = float(m['location']['accuracy'])

                person = {
                    'id': m['id'],
                    'name': m['firstName'] + ' ' + m['lastName'],
                    'nickname': m['firstName'],
                    'latitude': lat,
                    'longitude': lon,
                    'accuracy': acc,
                    'time': datetime.datetime.utcfromtimestamp(int(m['location']['timestamp'])).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'since': datetime.datetime.utcfromtimestamp(int(m['location']['since'])).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'address': None
                }


                for lname, l in locations.items():
                    d = distance_between(lat, lon, l['latitude'], l['longitude'])
                    if d + acc < l['radius']:
                        try:             person['address'] = l['address']
                        except KeyError: person['address'] = lname
                        break

                if not person['address']:
                    try:
                        if m['location']['address1']:
                            person['address'] = m['location']['address1']
                    except:
                        pass

                if not person['address']:
                    try:
                        location = geolocator.reverse("{}, {}".format(lat, lon))
                        if isinstance(location, list):
                            location = location[0]
                        if location:
                            addr = location.address
                            person['raw_address'] = addr
                            addr = re.sub(r'^\d+\s*([A-Z])', r'\1', addr)
                            person['address'] = addr
                    except Exception as err:
                        print (err)

                people[m['id']] = person
    return people

location_topic = "/location"

jsons = {}
try:
    while True:
        try:
            while True:
                people = get_updates()
                updated = False
                for pid, person in people.items():
                    j = json.dumps(person)

                    # Remove timestamp from comparison
                    #nj = re.sub('"time": "[^"]+",?\s+?', '', j)
                    #if pid not in jsons or jsons[pid] != nj:
                    if pid not in jsons or jsons[pid] != j:
                        #jsons[pid] = nj
                        jsons[pid] = j
                        updated = True

                        print(j)
                        if not debug:
                            mqtt.publish(location_topic + '/' + pid, j, retain=True)
                            mqtt.publish(location_topic + '/' + pid + '/updated', person['time'], retain=True)

                if updated:
                    time.sleep(60)
                else:
                    time.sleep(300)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print("LOOP EXCEPTION")
            raise e
            print(e)
            time.sleep(3)
except KeyboardInterrupt:
    pass
