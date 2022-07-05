from mycroft.util.format    import nice_date
from mycroft.util.parse     import extract_datetime
from icalendar              import Calendar, Event
from datetime               import datetime
from mycroft                import MycroftSkill, intent_handler
from pathlib                import Path
import os

class CalendarEvent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.INFINITIVE_SIGNS = ["att", "that"]
        self.CAL_PATH = Path(Path.home(), 'MagicMirror', 'modules', 'calendar', 'calendar.ics')
        self.calendar = self.initialize_calendar()

    def initialize_calendar(self) -> Calendar: 
        if self.calendar_exists():
            with self.file_system.open(self.CAL_PATH, "rb") as file:
                return Calendar.from_ical(file.read())
        else:
            self.CAL_PATH.parent.mkdir(parents=True, exist_ok=True)
            return Calendar()

    def calendar_exists(self):
        return self.file_system.exists(self.CAL_PATH) and os.stat(self.CAL_PATH).st_size > 0
    
    def contains_datetime(self, utterance):
        return extract_datetime(utterance) is not None

    def add_calendar_event(self, date_time:datetime, description:str):
        event = Event()
        event.add('description', description)
        event.add('dtstart', date_time)
        # event.add('rrule', {'freq': 'daily'}) TODO: Add functionality to add recurring events.
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
            self.speak_dialog('event.created', {'description': description, 'date_time': nice_date(date_time)})
            
    def get_datetime(self) -> datetime:
        date_time, response = (None, None)
        response = self.get_response('what.datetime', validator=self.contains_datetime, num_retries=-1)
        if type(response) is not str:
            raise TypeError(f'response cant be of type {type(response)} since a string is needed for extract_datetime')
        date_time = extract_datetime(response)[0]
        return date_time

    def clean_description(self, description:str) -> str:
        description = "" if description is None else description
        description = description.split(' ')
        if description[0].lower() in self.INFINITIVE_SIGNS:
            description.pop(0)
        description[0] = description[0].capitalize()
        return' '.join(description)

    def string_is_empty(self, string:str) -> bool:
        return not (string and string.strip())

    @intent_handler('create.event.intent')
    def create_event(self, message):
        event       = message.data.get('event')
        date_time   = None
        description = None

        try:
            if self.string_is_empty(event): # Empty: True
                date_time   = self.get_datetime()
                description = self.get_response('what.description')
            elif self.contains_datetime(event): # Empty: False, Datetime: True, Description: Maybe
                date_time, description = extract_datetime(event)
                if self.string_is_empty(description): # Description: False
                    description = self.get_response('what.description')
            elif (not (self.string_is_empty(event)) and not (self.contains_datetime(event))): # Empty: False, Datetime: False => Description: True
                date_time   = self.get_datetime()
                description = event
        except TypeError as error:
            self.speak_dialog("could.not.understand")
            self.log.error(error)
            return
        
        return self.add_calendar_event(date_time, self.clean_description(description))

def create_skill() -> CalendarEvent:
    return CalendarEvent()