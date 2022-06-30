from operator import contains
from mycroft import MycroftSkill, intent_handler
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from pathlib import Path
from pytz import timezone
import os

class CalendarEvent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.CAL_PATH = os.path.join(Path.home(), 'MagicMirror', 'modules', 'calendar', 'calendar.ics')
        
        self.calendar = self.initialize_calendar()
        # Some properties are required to be compliant
        # cal.add('prodid', '-//My calendar product//example.com//')
        # cal.add('version', '2.0')

        # event = Event()
        # event.add('name', 'Event name')
        # event.add('description', 'Event description')
        # event.add('dtstart', datetime(2022, 7, 1, 14, 0, 0, 0, tzinfo=tzlocal()))
        # event.add('dtend', datetime(2022, 7, 1, 15, 0, 0, 0, tzinfo=tzlocal()))
        
        # cal.add_component(event)

        # cal.add('prodid', '-//My calendar product//example.com//')
        # cal.add('version', '2.0')

        # Add subcomponents
        # event = Event()
        # event.add('name', 'Gin-provning!')
        # event.add('description', 'Beskrivning av Gin-provning')
        # event.add('dtstart', datetime(2022, 6, 30, 17, 0, 0, tzinfo=timezone("Europe/Stockholm")))
        # event.add('dtend', datetime(2022, 6, 30, 20, 0, 0, tzinfo=timezone("Europe/Stockholm")))
        
        # # Add the event to the calendar
        # cal.add_component(event)

        # # with open('example.ics', 'wb') as file:
        # #     file.write(cal.to_ical())
        # self.log.info(os.path.join(Path.home(), 'MagicMirror', 'modules', 'calendar', 'example.ics'))
        # with self.file_system.open(CAL_PATH, "wb") as my_file:
        #     my_file.write(cal.to_ical())
        # self.log.info(self.file_system.exists(CAL_PATH))
        # with self.file_system.open(CAL_PATH, "rb") as my_file:
        #     self.log.info(my_file.read())

    def initialize_calendar(self):
        if self.file_system.exists(self.CAL_PATH):
            with self.file_system.open(self.CAL_PATH, "rb") as file:
                return Calendar.from_ical(file.read())
        else:
            return Calendar()

    # Event containing description and datetime.
    @intent_handler('create.this.event.at.intent')
    def create_event(self, message):
        description = message.data.get('description', None)
        if description is None:
            return self.create_event_no_description(message)
        date_time, rest = self.extract_datetime(message.data.get('datetime', None))
        if date_time is None: #TODO: Handle case where padatious misses datetime in utterance.
            return self.create_event_no_datetime(message)
        event = Event()
        event.add('description', description)
        event.add('dtstart', date_time)
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
            
    # Event containing datetime.
    @intent_handler('create.event.at.intent')
    def create_event_no_description(self, message):
        if not self.contains_datetime(message.data['utterance']):
            return self.create_event_nothing(message)

    # Event containing description.
    @intent_handler('create.this.event.intent')
    def create_event_no_datetime(self, message):
        description = message.data.get('description', None)
        if description is None:
            return self.create_event_no_description(message)

    # Event containing nothing. 
    @intent_handler('create.event.intent')
    def create_event_nothing(self, message):
        pass

def create_skill():
    return CalendarEvent()

