from datetime import date, datetime, timedelta
from time import strftime

# from utils import list_of


def sys_time():
    return strftime("%H:%M:%S")


def utc_time():
    utc = datetime.utcnow()
    return utc.strftime("%H:%M:%S")


def short_date(dt):
    return dt.strftime("%d/%m/%y")


def short_date_and_time(dt):
    return dt.strftime("%d/%m/%y %H:%M:%S")


def long_date(dt):
    return dt.strftime("%d %b %Y")


def long_date_and_time(dt):
    return dt.strftime("%d %b %Y at %H:%M:%S")


def short_delta(td):
    parts = []

    if td.days != 0:
        parts.append(f"{td.days:,}d")

    if (h := td.seconds // 3600) != 0:
        parts.append(f"{h}h")

    if (m := td.seconds // 60 - 60 * h) != 0:
        parts.append(f"{m}m")

    if (s := td.seconds - 60 * m - 3600 * h) != 0:
        parts.append(f"{s}s")

    if len(parts) == 0:
        return "None"

    return ", ".join(parts)


def long_delta(td):
    parts = []

    if (d := td.days) != 0:

        parts.append(f"{d:,} day{'s' if d > 1 else ''}")

    if (h := td.seconds // 3600) != 0:
        parts.append(f"{h} hour{'s' if h > 1 else ''}")

    if (m := td.seconds // 60 - 60 * h) != 0:
        parts.append(f"{m} minute{'s' if m > 1 else ''}")

    if (s := td.seconds - 60 * m - 3600 * h) != 0:
        parts.append(f"{s} second{'s' if s > 1 else ''}")

    if len(parts) == 0:
        return "None"

    return list_of(parts)


def from_iso(stamp, dt=True):
    try:
        return datetime.fromisoformat(stamp) if dt else date.fromisoformat(stamp)

    except TypeError:
        # in case there's no records
        return datetime.min if dt else date.min


def to_iso(obj, dt=True):
    return obj.isoformat(" ") if dt else obj.isoformat()
