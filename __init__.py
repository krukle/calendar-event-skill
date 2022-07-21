from datetime               import time as _time
from datetime               import datetime
from mycroft.util.format    import nice_date
from mycroft.util.parse     import extract_datetime, match_one
from mycroft.messagebus     import Message
from icalendar              import Calendar, Event, vDatetime, vRecur
from mycroft                import MycroftSkill, intent_handler
from pathlib                import Path
import re
import pytz
import os

class CalendarEvent(MycroftSkill):
    def __init__(self):
        """Initialize the object for mycroft .
        """        
        MycroftSkill.__init__(self)
        self.MM_PATH            = Path(Path.home(), 'MagicMirror')
        self.CAL_MM_REL_PATH    = Path('modules', 'calendar', 'calendar.ics')
        self.CAL_PATH           = Path(self.MM_PATH, self.CAL_MM_REL_PATH)
        
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

    def initialize(self):
        self.calendar = self.initialize_calendar()

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
        return self.extract_datetime(utterance) is not None
    
    def contains_frequency(self, utterance:str) -> bool:
        """Returns True if the utterance contains a frequency."""
        return self.extract_frequency(utterance)[0] is not None

    def string_is_empty(self, string:str) -> bool:
        """Return True if the string is empty, only whitespace or not None."""        
        return not (string and string.strip())
    
    def nice_frequency(self, frequency:vRecur) -> str:
        """Generate nice frequency string for the given frequency vRecur object."""
        assert type(frequency) is vRecur, f"Frequency is of type {type(frequency)}, has to be of type vRecur."
        nice_frequency = self.translate_namedvalues('frequency', ',')[frequency.get('FREQ').lower()]
        if frequency.get('BYWEEKDAY') is not None:
            nice_frequency = " ".join((nice_frequency, self.translate_list('during')[0], (self.translate_list('weekdays')[0])))
        return nice_frequency

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
    
    def get_response_datetime(self) -> datetime:
        """Get a datetime object from user response .

        Returns:
            datetime: datetime object parsed from response.
        """
        response = self.get_response('what.datetime', validator=self.contains_datetime)
        assert response is not None, 'Execution was preempted since there was no reponse'
        return self.extract_datetime(response)[0]
    
    def extract_datetime(self, utterance:str) -> "tuple[datetime, str]":
        """ Wrapper for mycroft.util.parse.extract_datetime.
        Extract a datetime from a string.
        Improves time parse.

        Args:
            utterance (str): Utterance of which to parse datetime from.

        Returns:
            datetime: parsed datetime object.
            str: rest of utterance after datetime parse.
        """
        
        # Replace single length digits such as '9' or '7' with '900' or '700'
        # to avoid weird crash in extract_datetime().
        utterance = ' '.join([(u + ".00") if (u.isdigit() and len(u) <= 2) else u for u in utterance.lower().split()])

        date_time, rest = extract_datetime(utterance)
        date_time = date_time.replace(hour = 0, minute = 0)
        rest += " 1702"
        # If there's no time set in the returned date_time and the rest
        # string contains digits; look for the time in the rest.
        if (date_time.time() == _time() and re.search('\d', rest)):
            
            # Iterate words that contain digits in rest.
            for word in re.findall('\S*\d+\S*', rest.lower()):
                # Split word into list of digits separated by separators such as '.', ',' and '-'.
                digits = re.split(r'\D+', word)
                
                # Digits where written together without separators, e.g. 120315
                if len(digits) == 1:
                    time = digits[0]
                    if len(time) <=2:
                        date_time = date_time.replace(hour = int(time))
                    elif len(time) <= 4:
                        date_time = date_time.replace(hour = int(time[:-2]), minute = int(time[-2:]))
                    elif len(time) <= 6:
                        date_time = date_time.replace(hour = int(time[:-4]), minute = int(time[-4:-2]), second = int(time[-2:]))
                        
                # Digits where written separated by separators. E.g. 12-03-15 or 12,03.15
                elif len(digits) <= 3:
                    int_digits = list(map(int, digits))
                    if len(digits) >= 2:
                        date_time = date_time.replace(hour = int_digits[0], minute = int_digits[1])
                    if len(digits) == 3:
                        date_time = date_time.replace(second = int_digits[2])
            
                # If a time's been set; break. 
                if date_time.time() != _time():
                    break
        return date_time, ' '.join([word for word in rest.lower().split() if (word not in self.translate_list('time') and not re.search('\d', word))])
            
   
    def extract_frequency(self, utterance:str, score_limit:float=0.5) -> "tuple[vRecur, str]":
        """Extracts an icalendar.vRecur object frquency from string utterance.
        Whats leftover from the string is returned as a rest.
        
        If no frequency is found in string, None is returned.

        Args:
            utterance (str): String to parse for a frequency.
            score_limit (float): Defines wheter the frequency is defined a match or not.

        Returns:
            vRecur: Recurrence frequency. None if no frequency is found.
            str: Rest. None if no frequency is found.
        """
        if self.string_is_empty(utterance): 
            return (None, None)
        
        best_match      = ""
        best_score      = 0.0
        best_frequency  = ('',{})
        utterance       = utterance.lower()
        
        for frequency in self.FREQUENCIES:
            match, score = match_one(utterance, frequency[self.lang])
            best_match, best_score, best_frequency = (match, score, frequency) if (score >= best_score) else (best_match, best_score, best_frequency)
        
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
    
        return (frequency, ' '.join([x for x in utterance.split() if x not in best_match.split()])) if best_score >= score_limit else (None, None)

    def add_calendar_event(self, date_time:datetime, description:str, frequency:vRecur=None):
        """Add a calendar event to the calendar .

        Args:
            date_time (datetime): datetime object.
            description (str): description for event.
            frequency (vRecur, optional): If events is to recur; defines the frequency. Defaults to None.
        """        
        event = Event({
            'description':  description,
            'dtstart':      vDatetime(date_time.astimezone(pytz.timezone('Etc/UTC')))
            })
        
        dialog_data = {
            'description':  description, 
            'date_time':    nice_date(date_time),
            'frequency':    ""
                       }
        
        if frequency is not None:
            frequency.update({'dtstart': vDatetime(date_time.astimezone(pytz.timezone('Etc/UTC'))).to_ical()})
            event.add('rrule', frequency)
            dialog_data['frequency'] = self.nice_frequency(frequency)
            
        self.calendar.add_component(event)
        with self.file_system.open(self.CAL_PATH, "wb") as f:
            f.write(self.calendar.to_ical())
        
        self.speak_dialog('event.created', dialog_data)
        
        # Alert MM calendar that there's been an update.
        self.bus.emit(Message("RELAY:calendar:FETCH_CALENDAR", {"url": "https://localhost:8080/" + str(self.CAL_MM_REL_PATH)}))


    @intent_handler('create.event.intent')
    def create_event(self, message):
        event       = message.data.get('event')
        date_time   = None
        description = None
        frequency   = None

        try:
            # Datetime: False, Description: False, Frequency: False
            if self.string_is_empty(event): 
                date_time   = self.get_response_datetime()
                description = self.get_response('what.description')
                frequency = self.extract_frequency(self.get_response('what.frequency', validator=self.contains_frequency))[0] if self.ask_yesno('should.event.recur') == 'yes' else None
            
            #Datetime: True
            elif self.contains_datetime(event): 
                date_time, rest = self.extract_datetime(event)
                
                # Datetime: True, Description: False, Frequency: False
                if self.string_is_empty(rest): 
                    description = self.get_response('what.description')
                    frequency = self.extract_frequency(self.get_response('what.frequency', validator=self.contains_frequency))[0] if self.ask_yesno('should.event.recur') == 'yes' else None
                
                # Datetime: True, Description: True, Frequency: True
                elif self.contains_frequency(rest): 
                    frequency, description = self.extract_frequency(rest)
                    
                    # Datetime: True, Description: False, Frequency: True
                    if self.string_is_empty(description): 
                        description = self.get_response('what.description')
                
                # Datetime: True, Description: True, Frequency: False
                else: 
                    description = rest
                    frequency = self.extract_frequency(self.get_response('what.frequency', validator=self.contains_frequency))[0] if (self.ask_yesno('should.event.recur') == 'yes') else None
            
            #Datetime: False, Frequency: True
            elif self.contains_frequency(event): 
                frequency, description = self.extract_frequency(event)
                date_time = self.get_response_datetime()
                
                #Datetime: True, Description: False, Frequency: True
                if self.string_is_empty(description): 
                    description = self.get_response('what.description')
            
            #Datetime: False, Description True, Frequency: False
            else: 
                description = event
                date_time = self.get_response_datetime()
                frequency = self.extract_frequency(self.get_response('what.frequency', validator=self.contains_frequency))[0] if self.ask_yesno('should.event.recur') == 'yes' else None
        
        except AssertionError as assertion_error:
            self.speak_dialog("could.not.understand")
            self.log.error(assertion_error)
            return
        
        return self.add_calendar_event(date_time, self.nice_description(description), frequency)

def create_skill() -> CalendarEvent:
    return CalendarEvent()