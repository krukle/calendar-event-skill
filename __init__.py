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
        MycroftSkill.__init__(self)
        self.CAL_PATH = Path(Path.home(), 'MagicMirror', 'modules', 'calendar', 'calendar.ics')
        self.calendar = self.initialize_calendar()
        # TODO: Make this into dialog files?
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
        if self.calendar_exists():
            with self.file_system.open(self.CAL_PATH, "rb") as file:
                return Calendar.from_ical(file.read())
        else:
            self.CAL_PATH.parent.mkdir(parents=True, exist_ok=True)
            return Calendar()

    def calendar_exists(self) -> bool:
        return self.file_system.exists(self.CAL_PATH) and os.stat(self.CAL_PATH).st_size > 0
    
    def contains_datetime(self, utterance:str) -> bool:
        return extract_datetime(utterance) is not None
    
    def contains_frequency(self, utterance:str) -> bool:
        return self.extract_frequency(utterance) is not None
    
    def extract_frequency(self, utterance:str) -> "tuple[vRecur, str]":
        best_match = ""
        best_score = 0.0
        best_frequency = ('',{})
        utterance = utterance.lower()
        for frequency in self.FREQUENCIES:
            match, score = match_one(utterance, frequency[self.lang])
            best_match, best_score, best_frequency = (match, score, frequency) if (score >= best_score) else (best_match, best_score, best_frequency)
            utterance, best_match, best_score, frequency[self.lang]
        
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
        nice_frequency = ""
        event = Event()
        event.add('description', description)
        event.add('dtstart', vDatetime(date_time))
        if frequency is not None:
            event.add('rrule', frequency)
            nice_frequency = self.clean_frequency(frequency)
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
            self.speak_dialog('event.created', {'description': description, 'date_time': nice_date(date_time), 'frequency': nice_frequency})

    def clean_frequency(self, frequency):
        nice_frequency = self.translate_namedvalues('frequency', ',')[frequency.get('FREQ').lower()]
        if frequency.get('BYWEEKDAY') is not None:
            nice_frequency = " ".join((nice_frequency, self.translate_list('during')[0], (self.translate_list('weekdays')[0])))
        return nice_frequency
            
    def get_datetime(self) -> datetime:
        date_time, response = (None, None)
        response = self.get_response('what.datetime', validator=self.contains_datetime, num_retries=-1)
        if type(response) is not str:
            raise TypeError(f'response cant be of type {type(response)} since a string is needed for extract_datetime')
        date_time = extract_datetime(response)[0]
        return date_time

    def clean_description(self, description:str) -> str:
        description = "" if description is None else description
        description = description.split()
        if description[0].lower() in self.translate_list('infinitive.signs'):
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
        except TypeError as error:
            self.speak_dialog("could.not.understand")
            self.log.error(error)
            return

        return self.add_calendar_event(date_time, self.clean_description(description), frequency)

def create_skill() -> CalendarEvent:
    return CalendarEvent()