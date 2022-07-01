from datetime import datetime
from mycroft import MycroftSkill, intent_handler
from icalendar import Calendar, Event
from pathlib import Path
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

    def initialize_calendar(self) -> Calendar:
        if self.file_system.exists(self.CAL_PATH):
            with self.file_system.open(self.CAL_PATH, "rb") as file:
                return Calendar.from_ical(file.read())
        else:
            return Calendar()

    def add_event(self, description:str, date_time:datetime):
        event = Event()
        event.add('description', description)
        event.add('dtstart', date_time)
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
            self.speak_dialog('event.created', {'description': description}, {'date_time': self.nice_duration(date_time)})
            
    def get_datetime(self) -> datetime:
        date_time = None
        while date_time is None:
            response = self.get_response('what.datetime')
            date_time, rest = self.extract_datetime(response)
        return date_time

    def extract_info(self, event:str) -> "tuple[datetime, str]":
        date_time, description = self.extract_datetime(event)
        if date_time is None:
            date_time = self.get_datetime()
            description = event
        if description is None:
            description = self.get_response('what.description')
        return date_time, description
        
    # Event containing description and datetime.
    @intent_handler('create.this.event.at.intent')
    def create_event(self, message):
        event = message.data.get('event', None)
        if event is None:
            return self.create_event_nothing()
        date_time, description = self.extract_info(event)
        if description is None:
            return self.create_event_no_description(message)
        date_time, description = self.extract_datetime(message.data.get('datetime', None))
        if date_time is None: #TODO: Handle case where padatious misses datetime in utterance. This is not it. See: https://github.com/MycroftAI/skill-reminder/blob/cd1b5513837d2674db842a4c42aef19b80ee658f/__init__.py#L275
            return self.create_event_no_datetime(message)
        
        return self.add_event(description, date_time)

    # Event containing datetime.
    # @intent_handler('create.event.at.intent')
    def create_event_no_description(self, message):
        date_time, rest = self.extract_datetime(message.data.get('datetime', None))
        if date_time is None: #TODO: Handle case where padatious misses datetime in utterance. This is not it. See: https://github.com/MycroftAI/skill-reminder/blob/cd1b5513837d2674db842a4c42aef19b80ee658f/__init__.py#L275
            return self.create_event_nothing()
        description = self.get_response('what.description')
        return self.add_event(description, date_time)

    # Event containing description.
    # @intent_handler('create.this.event.intent')
    def create_event_no_datetime(self, message):
        description = message.data.get('description', None)
        if description is None:
            return self.create_event_no_description(message)
        date_time = self.get_datetime()
        return self.add_event(description, date_time)

    # Event containing nothing. 
    # @intent_handler('create.event.intent')
    def create_event_nothing(self):
        response = self.get_response('what.event')
        date_time, description = self.extract_info(response)
        return self.add_event(description, date_time)

def create_skill() -> CalendarEvent:
    return CalendarEvent()