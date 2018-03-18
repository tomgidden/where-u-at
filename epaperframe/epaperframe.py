#!/usr/bin/env python3

mqtt_host = 'mqtt.home'
import paho.mqtt.client as paho

from threading import Timer

import datetime
import dateutil.parser
import time
from pytz import timezone

import math

import os
import sys

import json
import re

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from image_utils import ImageText

# Home coordinates
home = (51.5014, 0.1419)


epd = None
try:
    import epd7in5
    epd = epd7in5.EPD()
    epd.init()
    debug = False
except ModuleNotFoundError:
    print ("Failed to find ePaper device")
    debug = True


screen_width = 640
screen_height = 384

name_size = 42
name_font = 'fonts/MyriadPro-Semibold.otf'

time_size = 20
time_font = 'fonts/MyriadPro-Cond.otf'

addr_size = 32
addr_font = 'fonts/MyriadPro-Cond.otf'

dist_size = 32
dist_font = 'fonts/MyriadPro-Cond.otf'

calday_size = 24
calday_font = 'fonts/MyriadPro-Semibold.otf'

today_size = 24
today_font = 'fonts/MyriadPro-Bold.otf'

eventname_size = 20
eventname_font = 'fonts/MyriadPro-Regular.otf'

eventnameno_size = 20
eventnameno_font = 'fonts/MyriadPro-It.otf'

eventtime_size = 18
eventtime_font = 'fonts/MyriadPro-Bold.otf'

eventname_tab = eventname_size * 4


#name_font = 'fonts/DIN Black.ttf'
#time_font = 'fonts/DIN Condensed Bold.ttf'
#addr_font = 'fonts/DIN Condensed Bold.ttf'
#dist_font = 'fonts/DIN Condensed Bold.ttf'
#calday_font = 'fonts/DIN Condensed Bold.ttf'
#eventname_font = 'fonts/DIN Condensed Bold.ttf'
#eventtime_font = 'fonts/DIN Condensed Bold.ttf'

margin_left = 10
margin_top = 10
margin_block = 20
margin_whereis_top = margin_top
margin_events_top = margin_top

left_x0 = margin_left
left_box_width = screen_width/2-margin_left*3

right_box_width = screen_width/2-margin_left*3
right_x0 = screen_width - right_box_width - margin_left

odump = None
dump = ""


changed = False
timer = None

location_topic = '/location';
people = {}

calendar_topic = '/calendar/all_events';
events = []

tz = timezone('Europe/London')



def on_connect(mqtt, userdata, flags, rc):
    global location_topic
    global calendar_topic
    if rc != 0:
        print("MQTT refused: "+str(rc))
        return
    mqtt.subscribe(location_topic+"/+", 0)
    mqtt.subscribe(calendar_topic, 0)

def on_disconnect (mqtt, userdata, rc):
    if 0 == rc:
        return
    elif rc is not None:
        print("MQTT disconnection: "+str(rc))

    try:
        print("MQTT reconnecting...")
        mqtt.reconnect()

    except Exception as e:
        print("MQTT error: "+str(e))
        pass

    return mqtt

def on_message(mqtt, obj, msg):
    global location_topic
    global calendar_topic
    global people
    global events
    global timer
    global changed

    print ("Got message {}".format(msg.topic))
    if msg.topic.startswith(location_topic):
        person = json.loads(msg.payload.decode('UTF-8'))
        try:
            operson = people[person['id']]
        except:
            operson = None
        person['time'] = datetime.datetime.strptime(person['time'], "%Y-%m-%dT%H:%M:%SZ")
        person['since'] = datetime.datetime.strptime(person['since'], "%Y-%m-%dT%H:%M:%SZ")
        people[person['id']] = person
        if person != operson: changed = True

    elif msg.topic == calendar_topic:
        oevents = events
        events = json.loads(msg.payload.decode('UTF-8'))
        if oevents != events: changed = True

    if changed:
        if timer is not None: timer.cancel()
        timer = Timer(1, redraw)
        timer.start()

def distance_from_home(lat, lon):
    global home
    hlat, hlon = home

    theta = hlon - lon
    dist = math.sin(lat*3.1415927/180.0) * math.sin(hlat*3.1415927/180.0) + math.cos(lat*3.1415927/180.0) * math.cos(hlat*3.1415927/180.0) * math.cos(theta*3.1415927/180.0);
    dist = math.acos(dist);
    dist = dist*180.0/3.1415927
    metres = dist * 60 *  1853;
    miles = metres * 0.000621371

    #    if miles <= 0.1:
    #        return "here"
    #    if metres < 804:
    #        return "{:d} metres".format(int(metres))
    if miles < 0.1:
        return "HOME"
    elif miles < 100:
        return "{:.1f} mi".format(miles)
    else:
        return "{} mi".format(int(miles+0.5))

def latlon_to_dms(lat, lon):
    if lat is None or lon is None: return ""

    lad = 'N'
    if lat < 0:
        lad = 'S'
        lat = -lat

    lai = int(lat)
    laf = math.fmod(lat, 1)
    tmp = laf*3600
    lam = math.floor(tmp/60)
    las = tmp - lam*60

    lod = 'E'
    if lon < 0:
        lod = 'W'
        lot = -lon

    loi = int(lon)
    lof = math.fmod(lon, 1)
    tmp = lof*3600
    lom = math.floor(tmp/60)
    los = tmp - lom*60

    return ("{}°{}'{:.2f}\" {}, {}°{}'{:.2f}\" {}".format(
        lai, lam, las, lad,
        loi, lom, los, lod
    ))

def draw_whereis(draw, people):
    global dump

    tdraw = ImageText(draw)

    x0 = left_x0
    box_width = left_box_width
    y = margin_whereis_top

    for person in sorted(people.values(), key=lambda p: p['name'], reverse=False):

        if y != margin_whereis_top:
            draw.line((x0, y - margin_top, box_width+x0, y - margin_top), fill=0)

        text = person['name'].split(None,1)[0]
        #draw.text((margin_left, y), text, name_font, name_size)
        tdraw.text_box(
            (x0, y),
            text,
            box_width=box_width,
            font_filename=name_font,
            font_size=name_size,
            #background=255,
            color=0
        )
        dump += "\n{},{},{}".format(text,margin_left,y)


        text = 'Since '+person['since'].strftime("%a, %H:%M")
        tdraw.text_box(
            (x0, y),
            text,
            box_width=box_width,
            font_filename=time_font,
            font_size=time_size,
            color=0,
            place='right'
        )
        dump += "\n{},{},{}".format(text,margin_left,y)

        y += name_size

        try:
            text = person['address']
        except Exception as e:
            print(e)
            try:
                text = person['raw_address']
            except:
                text = latlon_to_dms(person['latitude'], person['longitude'])

        text = re.sub(r'([A-Z]{1,2}[0-9]{1,2}[A-Z]?) ([0-9][A-Z]{2})',
                      r'\1 \2',
                      text)

        if (text != 'Home'):
            width, height = tdraw.text_box(
                (x0, y),
                text,
                box_width=box_width,
                font_filename=addr_font,
                font_size=addr_size,
                lines_limit=2,
                color=0
            )
            dump += "\n{},{},{}".format(text,margin_left,y)
        y += addr_size*1.1

        if True or (text != 'HOME'):
            text = distance_from_home(person['latitude'], person['longitude'])
            tdraw.text_box(
                (x0, y),
                "  "+text,
                box_width=box_width,
                font_filename=dist_font,
                font_size=dist_size,
                color=0,
                background=255,
                margin=2,
                place='right'
            )
            tdraw.text_box(
                (x0, y),
                text,
                box_width=box_width,
                font_filename=dist_font,
                font_size=dist_size,
                color=255,
                background=0,
                margin=2,
                place='right'
            )

        dump += "\nright\t{},{},{}".format(text,margin_left,y)

        y += addr_size*1.1
        y += margin_block
        dump += "\n---"

def draw_events(draw, events):
    global dump

    tdraw = ImageText(draw)

    x0 = right_x0
    box_width = right_box_width
    y = margin_events_top

    draw.line((screen_width/2, 0, screen_width/2, screen_height), fill=0)


    now = datetime.datetime.now().replace(tzinfo=tz) + datetime.timedelta(days=0)
    midnight = datetime.datetime.combine(now, datetime.time(0,0,0,tzinfo=tz))

    # First, separate out into days
    daysevents = {}
    daysevents[0] = []
    daysevents[1] = []

    i = 0
    oday = None
    for event in events:
        td = dateutil.parser.parse(event['begin'])
        otd = td

        if (type(td) == datetime.date):
            if td < datetime.today():
                td = midnight
        elif td < midnight:
            td = midnight

        until = td - midnight
        day = until.days

        if oday != day:
            daysevents[day] = []
            oday = day
        daysevents[day].append(event)
        i += 1
        if i > 20: break

    oday = ""
    dnum = 0
    for dnum, events in daysevents.items():
        events.sort(key=lambda e: e['begin'])

        x = now + datetime.timedelta(days=dnum)
        day = x.strftime("%A %d %B").replace(" 0", " ")

        font = calday_font
        size = calday_size

        if dnum == 0:
            day = now.strftime("%A, %d %B").replace(" 0", " ")
#            day = 'Saturday, 23 September'
            font = today_font
            size = today_size
        elif dnum == 1:
            day = "Tomorrow ("+x.strftime("%A")+")"

        tdraw.text_box(
            (x0, y),
            day,
            box_width=box_width,
            font_filename=font,
            font_size=size,
            place="center",
            #background=255,
            color=0
        )
        dump += "\n{},{},{}".format(day,x0,y)
        y += size * 1.2


        if not events:
            text = 'No events scheduled'
            tdraw.text_box(
                (x0, y),
                text,
                box_width=box_width,
                font_filename=eventnameno_font,
                font_size=eventnameno_size,
                place="center",
                #background=255,
                color=0
            )
            dump += "\n{},{},{},{}".format(day,text,x0+eventname_tab,y)
            y += eventnameno_size * 1.2

        else:
            for event in events:
                i += 1

                if y > screen_height: return

                td = dateutil.parser.parse(event['begin'])
                otd = td

                if (type(td) == datetime.date):
                    if td < datetime.today():
                        td = midnight
                elif td < midnight:
                    td = midnight

                text = event['title']
                text = re.sub(r'^\d{1,2}:\d{2}\s*', '', text)

                (w,h) = tdraw.text(
                    (x0 + eventname_tab, y),
                    text,
                    font_filename=eventname_font,
                    font_size=eventname_size,
                    #background=255,
                    color=0
                )

                if (x0 + eventname_tab + w > screen_width):
                    tdraw.text_box(
                        (x0, y),
                        "…",
                        box_width=box_width+margin_left,
                        font_filename=eventname_font,
                        font_size=eventname_size,
                        place="left",
                        background=255,
                        color=0
                    )
                    dump += "\n{},{},{}".format('...',x0,y)

                timetext = '?'
                if event['allday']:
                    if (otd != td):
                        timetext = '…'
                    else:
                        timetext = ''
                else:
                    try:
                        timetext = dateutil.parser.parse(event['begin']).strftime("%H:%M")

                    except:
                        pass

                tdraw.text(
                    (x0, y),
                    timetext,
                    font_filename=eventtime_font,
                    font_size=eventtime_size,
                    #background=255,
                    color=0
                )

                dump += "\n{},{}:{},{},{}".format(day,timetext,text,x0+eventname_tab,y)
                y += eventname_size * 1.2
        y += margin_top
        draw.line((x0, y - margin_top, x0+box_width, y - margin_top), fill=0)

def redraw():

    global changed
    global odump, dump
    global people
    global events
    global epd
    global timer

    timer = None
    print ("Redraw starts")

    if changed:
        changed = False

        image = Image.new('1', (screen_width, screen_height), 1)    # 1: clear the frame
        draw = ImageDraw.Draw(image)

        odump = dump
        dump = ""

        draw_whereis(draw, people)
        draw_events(draw, events)

        print("Drawing done")

        if dump == odump:
            print ("No actual change")
        else:
            print("Writing out")
            if epd:
                buffer = epd.get_frame_buffer(image.rotate(180))
                print("Framebuffer generated")

                epd.display_frame(buffer)
                print("Sent to display")
                image.save('/nfs/scratch/epaperframe.png')
            else:
                image.show()

mqtt = paho.Client()
mqtt.on_connect = on_connect
mqtt.on_message = on_message
mqtt.on_disconnect = on_disconnect
mqtt.connect(mqtt_host, 1883, 60)
mqtt.loop_forever()

#epd.display_frame(imagedata.MONOCOLOR_BITMAP)
