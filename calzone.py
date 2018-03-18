#!/usr/bin/env python3

import copy
from types import SimpleNamespace
from icalendar import Calendar
from pytz import timezone, utc
from dateutil.rrule import *
from dateutil.tz import tzoffset
import datetime
import email.utils
import calendar
import json

class Event(SimpleNamespace):
    def __str__(self):
        return json.dumps({
            'title': self.summary,
            'begin': str(self.start),
            'end': str(self.end),
            'allday': self.all_day
        })

class Calzone:

    def __init__(self, tz='Europe/London'):
        self.localtz = timezone(tz)
        self.events = []
        self.oneday = datetime.timedelta(days=1)
        self.onehour = datetime.timedelta(hours=1)
        self.onesec = datetime.timedelta(seconds=1)

    def midnight():
        return datetime.combine(datetime.now(), time(0,0,0,tzinfo=self.localtz))

    def to_datetime(self, dt, endofday=False):
        if type(dt) is datetime.datetime:
            if dt.tzinfo:
                return dt
            else:
                return self.localtz.localize(dt)

        if type(dt) is datetime.date:
            if endofday:
                return datetime.datetime.combine(dt, datetime.time(23,59,59,tzinfo=self.localtz))
            else:
                return datetime.datetime.combine(dt, datetime.time(0,0,0,tzinfo=self.localtz))

        return None

    def load(self, ical):

        cal = Calendar.from_ical(ical)

        for e in cal.walk('VEVENT'):
            e_begin = e.get('dtstart').dt
            e_begin = self.to_datetime(e_begin)

            try:
                e_end = e.get('dtend').dt
                e_end = self.to_datetime(e_end)
            except:
                e_end = e_begin + self.onehour

            event = Event()
            event.start = e_begin
            event.end = e_end
            event.summary = str(e.get('summary'))
            event.description = str(e.get('description'))
            event.all_day = type(e.get('dtstart').dt) is datetime.date

            event.exdate = e.get('exdate', [])
            if not isinstance(event.exdate, list):
                event.exdate = [event.exdate]

            rr = e.get('rrule')
            if rr:
                event.rr = rr.to_ical().decode('UTF-8')
            else:
                event.rr = None

            event.raw = e
            self.events.append(event)

    def get_events(self, start=None, end=None):
        if not start:  start = datetime.now()
        else:          start = self.to_datetime(start)

        if end:        end = self.to_datetime(end)

        self.events.sort(key=lambda e: e.start)

        def get_tz(tz, off):
            if tz is None or off is None: return self.localtz
            return tzoffset(tz, off)

        ret = []
        for event in self.events:
            if event.rr:
                rules = rruleset()
                s = rrulestr(event.rr, dtstart=event.start, tzinfos=get_tz)
                rules.rrule(s)
                for x in event.exdate:
                    try:
                        rules.exdate(self.to_datetime(x.dts[0].dt))
                    except Exception as err:
                        print("Bad exdate: {}".format(err))
                        raise err

                if start:
                    if end:
                        rs = rules.between(start, end, True)
                    else:
                        rs = rules.after(start, True)
                elif end:
                    rs = rules.before(end, True)
                else:
                    rs = []

                if rs:
                    if type(rs) != list:
                        rs = [rs]
                    for r in rs:
                        ne = copy.copy(event)
                        dur = ne.end - ne.start
                        ne.start = r
                        ne.end = r + dur
                        ret.append(ne)
            else:
                if event.end < start:         continue
                if end and event.start > end: continue
                ret.append(event)
        return ret

if __name__ == "__main__":

    tz = timezone('Europe/London')
    now = datetime.datetime.now().replace(tzinfo=tz)
    midnight = datetime.datetime.combine(now, datetime.time(0,0,0,tzinfo=tz))

    cz = Calzone()

    buf = open('test.ics', 'r', encoding='utf-8').read()
    cz.load(buf)

    for i in range(0,7):
        t0 = midnight + i * cz.oneday
        t1 = t0 + cz.oneday - cz.onesec

        print("---")
        for e in cz.get_events(t0, t1):
            print ("{}\t{}\t{}".format(e.start, e.end, e.summary))
            if hasattr(e,'rec'):
                print(e.rr)
                print(e.rec)
