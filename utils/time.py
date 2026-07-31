from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def hoje_inicio_utc():
    return utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def inicio_mes_utc():
    return utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def naive_dt(dt):
    if dt and dt.tzinfo:
        return dt.replace(tzinfo=None)
    return dt
