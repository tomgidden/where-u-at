#!/usr/bin/env python3


from config import *

import paho.mqtt.client as paho

import time
import requests
import os
import sys
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

def get_forecast():
    r = requests.get('http://api.openweathermap.org/data/2.5/forecast?id={}&APPID={}'.format(city_id, weather_api_key))
    return r.json()


weather_topic = "/weather"

j = None
try:
    while True:
        try:
            while True:
                oj = j
                j = json.dumps(get_forecast())

                if j == oj:
                    time.sleep(refresh)
                else:
                    print("Publishing...")
                    print(j)
                    if not debug:
                        mqtt.publish(weather_topic, j, retain=True)
                        mqtt.publish(weather_topic + "/updated", int(time.time()), retain=True)
                    time.sleep(3600)
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print("LOOP EXCEPTION")
            raise e
            print(e)
            time.sleep(3)
except KeyboardInterrupt:
    pass
