import dataclasses
import datetime
import typing

import timespans


class SourceLine:
    """
    Single source file representation
    """
    def _parse(self):
        pass

    def __init__(self, line):
        self.line = line
        self._parse()

    @property
    def name(self) -> str:
        return 'unnamed'



@dataclasses.dataclass
class Periodic:
    start_time: datetime.time
    specs: typing.List[str]

    def has_day(self, day: datetime.date) -> bool:
        DAYS = [
            ['понедельник', 'monday'],
            ['вторник', 'tuesday'],
            ['среда', 'wednesday'],
            ['четверг', 'thursday'],
            ['пятница', 'friday'],
            ['суббота', 'saturday'],
            ['воскресенье', 'sunday']
        ]
        result = any(d in self.specs for d in DAYS[day.weekday()])
        return result

    def get_timespan_for_day_duration(self, day, duration_hours: int):
        start = datetime.datetime.combine(day, self.start_time)
        return timespans.TimeSpan(start=start,
                                  end=start + datetime.timedelta(hours=duration_hours))
