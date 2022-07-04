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

    def add_calendar_event(self, description:str, date_time:datetime):
        event = Event()
        event.add('description', description)
        event.add('dtstart', date_time)
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
            self.speak_dialog('event.created', {'description': description, 'date_time': nice_date(date_time)})
            
    def get_datetime(self) -> datetime:
        date_time, response = (None, None)
        # while date_time is None or response is None or self.voc_match(response, 'cancel'):
            # self.log.info(self.voc_match(response, 'cancel'), response)
            #TODO: Fix the check
        response = self.get_response('what.datetime')
        date_time, rest = extract_datetime(response) or (None, None)
        return date_time

    def extract_info(self, event:str) -> "tuple[datetime, str]":
        if event is not None:
            date_time, description = extract_datetime(event)
        else:
            date_time, description = None, None
        if date_time is None:
            date_time = self.get_datetime()
            description = next((item for item in [description, event] if item is not None), None) # set description to whichever isn't None of description and event.
        if description is None:
            description = self.get_response('what.description')
        return date_time, description
        
    # Event containing description and datetime.
    @intent_handler('create.event.intent')
    def create_event(self, message):
        date_time, description = self.extract_info(message.data.get('event', None))
        return self.add_calendar_event(description, date_time)

def create_skill() -> CalendarEvent:
    return CalendarEvent()