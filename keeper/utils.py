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
