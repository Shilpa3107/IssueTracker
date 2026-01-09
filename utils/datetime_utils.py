from datetime import datetime

def utc_now():
    """Return current UTC datetime"""
    return datetime.utcnow()

def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S"):
    """Return formatted datetime string"""
    if dt:
        return dt.strftime(fmt)
    return None

def hours_between(start: datetime, end: datetime) -> float:
    """Return difference in hours between two datetimes"""
    return (end - start).total_seconds() / 3600
