# <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/svgs/regular/calendar-check.svg" card_color="#40DBB0" width="50" height="50" style="vertical-align:bottom"/> Calendar Event

Adds calendar events to the stock MagicMirror module.

## Dependencies

```bash
mycroft-pip install pytz icalendar
```

## Installation

```bash
git clone git@github.com:krukle/calendar-event-skill.git ~/mycroft-core/skills/calendar-event-skill
```

> **Note**
>
> Change git clone destination according to your setup.

## Message

| Message | Data | About |
| ------- | ---- | ----- |
| FETCH_CALENDAR | `{"url": str}` | Emitted when calendar should be updated. `url` is url to calendar ics file. |

## Command

### Create a calendar event

| English | Swedish |
| ------- | ------- |
| "Create a calendar event `event`" | "Skapa en händelse `event`" |
| "Plan an event `event`" | "Lägg till i kalendern `event`" |

`event` contains four variables; *name*, *date*, *description* and *freqeuncy*. All variables will be extracted from `event`, and if any is not recognized, Mycroft will request it.
