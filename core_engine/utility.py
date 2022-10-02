import datetime, time


def get_current_utc_datetime():
    return datetime.datetime.utcnow()


def get_current_datetime():
    return datetime.datetime.now()


def get_current_epoch():
    return int(time.time())
