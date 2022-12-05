import datetime
import os


def days(datefrom, dateto):
    datenow = datefrom
    while datenow < dateto:
        yield datenow
        datenow += datetime.timedelta(days=1)


def mkdir_p(path):
    """
    create directory {path} if necessary
    """
    if os.path.exists(path) and os.path.isdir(path):
        return

    os.makedirs(path)


ONE_DAY = datetime.timedelta(days=1)


def td_to_hours(td: datetime.timedelta):
    """
    :type td: timedelta
    """
    day_hours = td.days * 24
    full_hours = int(float(td.seconds) / 3600)
    remaining_hours = float(td.seconds % 3600) / 3600
    hours = (day_hours + full_hours + remaining_hours)
    return round(hours, 2)
