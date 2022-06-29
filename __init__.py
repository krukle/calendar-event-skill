from mycroft import MycroftSkill, intent_handler


class CalendarEvent(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_handler('event.calendar.intent')
    def handle_event_calendar(self, message):
        self.speak_dialog('event.calendar')


def create_skill():
    return CalendarEvent()

