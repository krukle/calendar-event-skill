from multiprocessing.context import assert_spawning
from typing import Tuple
from mycroft.util.format    import nice_date
from mycroft.util.parse     import extract_datetime, match_one
from icalendar              import Calendar, Event, vDatetime, vRecur
from datetime               import datetime
from mycroft                import MycroftSkill, intent_handler
from pathlib                import Path
import os

class CalendarEvent(MycroftSkill):
    def __init__(self):
        """Initialize the object for mycroft .
        """        
        MycroftSkill.__init__(self)
        self.CAL_PATH = Path(Path.home(), 'MagicMirror', 'modules', 'calendar', 'calendar.ics')
        self.calendar = self.initialize_calendar()
        
        # TODO: Make this into a /dialog files
        self.FREQ_DAILY = {
            "en-us": ["daily", "every day"],
            "sv-se": ["dagligen", "varje dag"]
        }
        self.FREQ_WEEKDAYS = {
            "en-us": ["weekdays", "every weekday"],
            "sv-se": ["vardagar", "varje vardag"]
        }
        self.FREQ_WEEKLY = {
            "en-us": ["weekly", "every week"],
            "sv-se": ["veckoligen", "varje vecka"]
        }
        self.FREQ_MONTHLY = {
            "en-us": ["monthly", "every month"],
            "sv-se": ["månatligen", "varje månad"]
        }
        self.FREQ_YEARLY = {
            "en-us": ["yearly", "every year"],
            "sv-se": ["årligen", "varje år"]
        }
        self.FREQUENCIES = [self.FREQ_DAILY, self.FREQ_WEEKDAYS, self.FREQ_WEEKLY, self.FREQ_MONTHLY, self.FREQ_YEARLY]

    def initialize_calendar(self) -> Calendar: 
        """Initialize the Calendar.
        
        If the calendar already exists, initializes from existing one.
        
        If not, a new calendar is created incl. parent folders."""  
        if self.calendar_exists():
            with self.file_system.open(self.CAL_PATH, "rb") as file:
                return Calendar.from_ical(file.read())
        else:
            self.CAL_PATH.parent.mkdir(parents=True, exist_ok=True)
            return Calendar()

    def calendar_exists(self) -> bool: 
        """Returns True if the calendar and its parent folders exists ."""            
        return self.file_system.exists(self.CAL_PATH) and os.stat(self.CAL_PATH).st_size > 0
    
    def contains_datetime(self, utterance:str) -> bool:
        """Returns True if the utterance contains a datetime object ."""        
        return extract_datetime(utterance) is not None
    
    def contains_frequency(self, utterance:str) -> bool:
        """Returns True if the utterance contains a frequency."""
        return self.extract_frequency(utterance) is not None
    
    def extract_frequency(self, utterance:str) -> "tuple[vRecur, str]":       
        """Extracts an icalendar.vRecur object frquency from string utterance.
        Whats leftover from the string is returned as a rest.
        
        If no frequency is found in string, None is returned.

        Args:
            utterance (str): String to parse for a frequency.

        Returns:
            tuple[vRecur, str]: Recurrence frequency and rest. None if no frequency is found.
        """        
        assert not self.string_is_empty(utterance), "Execution was preempted since frequency was empty"
        best_match = ""
        best_score = 0.0
        best_frequency = ('',{})
        utterance = utterance.lower()
        for frequency in self.FREQUENCIES:
            match, score = match_one(utterance, frequency[self.lang])
            best_match, best_score, best_frequency = (match, score, frequency) if (score >= best_score) else (best_match, best_score, best_frequency)
            utterance, best_match, best_score, frequency[self.lang]
        
        # DOCS: https://dateutil.readthedocs.io/en/stable/rrule.html
        if best_frequency == self.FREQ_DAILY:
            frequency = vRecur({'freq': 'daily', 'interval': 1})
        elif best_frequency == self.FREQ_WEEKDAYS:
            frequency = vRecur({'freq': 'daily', 'interval': 1, 'byweekday':range(6)})
        elif best_frequency == self.FREQ_WEEKLY:
            frequency = vRecur({'freq': 'weekly', 'interval': 1})
        elif best_frequency == self.FREQ_MONTHLY:
            frequency = vRecur({'freq': 'monthly', 'interval': 1})
        elif best_frequency == self.FREQ_YEARLY:
            frequency = vRecur({'freq': 'yearly', 'interval': 1})

        return (frequency, ' '.join([x for x in utterance.split() if x not in best_match.split()])) if best_score >= 0.5 else None

    def add_calendar_event(self, date_time:datetime, description:str, frequency:vRecur=None):
        """Add a calendar event to the calendar .

        Args:
            date_time (datetime): datetime object.
            description (str): description for event.
            frequency (vRecur, optional): If events is to recur; defines the frequency. Defaults to None.
        """        
        nice_frequency = ""
        event = Event()
        event.add('description', description)
        event.add('dtstart', vDatetime(date_time))
        if frequency is not None:
            event.add('rrule', frequency)
            nice_frequency = self.nice_frequency(frequency)
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
            self.speak_dialog('event.created', {'description': description, 'date_time': nice_date(date_time), 'frequency': nice_frequency})

    def nice_frequency(self, frequency:vRecur) -> str:
        """Generate nice frequency string for the given frequency vRecur object."""     
        nice_frequency = self.translate_namedvalues('frequency', ',')[frequency.get('FREQ').lower()]
        if frequency.get('BYWEEKDAY') is not None:
            nice_frequency = " ".join((nice_frequency, self.translate_list('during')[0], (self.translate_list('weekdays')[0])))
        return nice_frequency
            
    def get_datetime(self) -> datetime:
        """Get a datetime object from user response .

        Returns:
            datetime: datetime object parsed from response.
        """
        date_time, response = (None, None)
        response = self.get_response('what.datetime', validator=self.contains_datetime)
        assert response is not None, 'Execution was preempted since there was no reponse'
        date_time = extract_datetime(response)[0]
        return date_time

    def nice_description(self, description:str) -> str:
        """Convert the ugly description to a nice string .

        Args:
            description (str): Ugly description.

        Returns:
            str: Nice description.
        """        
        assert not self.string_is_empty(description), "Execution was preempted since description was empty"
        description = description.lower().split()
        if description[0] in self.translate_list('infinitive.signs'):
            description.pop(0)
        description[0] = description[0].capitalize()
        return' '.join(description)

    def string_is_empty(self, string:str) -> bool:
        """Return True if the string is empty, only whitespace or not None."""        
        return not (string and string.strip())

    @intent_handler('create.event.intent')
    def create_event(self, message):
        event       = message.data.get('event')
        date_time   = None
        description = None
        frequency   = None

        try:
            if self.string_is_empty(event): # Datetime: False, Description: False, Frequency: False
                date_time   = self.get_datetime()
                description = self.get_response('what.description')
                frequency = self.get_response('what.frequency', validator=self.contains_frequency) if self.ask_yesno('should.event.recur') == 'yes' else None
            elif self.contains_datetime(event): #Datetime: True
                date_time, rest = extract_datetime(event)
                if self.string_is_empty(rest): # Datetime: True, Description: False, Frequency: False
                    description = self.get_response('what.description')
                    frequency = self.get_response('what.frequency', validator=self.contains_frequency) if self.ask_yesno('should.event.recur') == 'yes' else None
                elif self.contains_frequency(rest): # Datetime: True, Description: True, Frequency: True
                    frequency, description = self.extract_frequency(rest)
                    if self.string_is_empty(description): # Datetime: True, Description: False, Frequency: True
                        description = self.get_response('what.description')
                else: # Datetime: True, Description: True, Frequency: False
                    description = rest
                    frequency = self.get_response('what.frequency', validator=self.contains_frequency) if self.ask_yesno('should.event.recur') == 'yes' else None
            elif self.contains_frequency(event): #Datetime: False, Description: True, Frequency: True
                date_time = self.get_datetime()
                frequency, description = self.extract_frequency(rest, rest=True) if self.ask_yesno('should.event.recur') == 'yes' else (None, None)
                if self.string_is_empty(description): #Datetime: False, Description: False, Frequency: True
                    description = self.get_response('what.description')
            else: #Datetime: False, Description True, Frequency: False
                date_time = self.get_datetime()
                description = event
                frequency = self.get_response('what.frequency', validator=self.contains_frequency) if self.ask_yesno('should.event.recur') == 'yes' else None
        except AssertionError as assertion_error:
            self.speak_dialog("could.not.understand")
            self.log.error(assertion_error)
            return

        return self.add_calendar_event(date_time, self.nice_description(description), frequency)

def create_skill() -> CalendarEvent:
    return CalendarEvent()