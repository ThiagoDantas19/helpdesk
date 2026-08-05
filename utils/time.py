import os
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo


def utcnow():
    return datetime.now(timezone.utc)


def fuso_padrao():
    return ZoneInfo(os.environ.get('APP_TIMEZONE', 'America/Sao_Paulo'))


def hora_local(dt):
    if not dt:
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(fuso_padrao()).replace(tzinfo=None)


def hoje_inicio_utc():
    inicio_local = hora_local(utcnow()).replace(hour=0, minute=0, second=0, microsecond=0)
    return inicio_local.replace(tzinfo=fuso_padrao()).astimezone(timezone.utc)


def inicio_mes_utc():
    inicio_local = hora_local(utcnow()).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return inicio_local.replace(tzinfo=fuso_padrao()).astimezone(timezone.utc)


def intervalo_dia_local_para_utc(data_str):
    """Converte 'AAAA-MM-DD' (dia local) no intervalo [inicio, fim) em UTC."""
    data = datetime.strptime(data_str, '%Y-%m-%d').date()
    inicio_local = datetime.combine(data, time.min).replace(tzinfo=fuso_padrao())
    fim_local = datetime.combine(data + timedelta(days=1), time.min).replace(tzinfo=fuso_padrao())
    return inicio_local.astimezone(timezone.utc), fim_local.astimezone(timezone.utc)
