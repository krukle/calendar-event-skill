from mycroft import MycroftSkill, intent_handler
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from pathlib import Path
from pytz import timezone
import os
import time

# Gets machines timezone accounting for daylight saving time.
TIME_ZONE = time.tzname[time.daylight]

class CalendarEvent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

        cal = Calendar()
        # Some properties are required to be compliant
        cal.add('prodid', '-//My calendar product//example.com//')
        cal.add('version', '2.0')

        event = Event()
        event.add('name', 'Event name')
        event.add('description', 'Event description')
        event.add('dtstart', datetime(2022, 6, 30, 14, 0, 0, 0, tzinfo=TIME_ZONE))
        event.add('dtend', datetime(2022, 6, 30, 15, 0, 0, 0, tzinfo=TIME_ZONE))
        
        cal.add_component(event)

        with open('example.ics', 'wb') as file:
            file.write(cal.to_ical())


    @intent_handler('event.calendar.intent')
    def handle_event_calendar(self, message):
        self.speak_dialog('event.calendar')


def create_skill():
    return CalendarEvent()

