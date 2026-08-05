from datetime import datetime, timezone, timedelta
from utils.time import hora_local, utcnow, hoje_inicio_utc, inicio_mes_utc, intervalo_dia_local_para_utc


def test_hora_local_converte_aware_utc_para_sao_paulo():
    dt = datetime(2026, 7, 31, 15, 31, tzinfo=timezone.utc)
    assert hora_local(dt) == datetime(2026, 7, 31, 12, 31)


def test_hora_local_trata_naive_como_utc():
    dt = datetime(2026, 7, 31, 15, 31)
    assert hora_local(dt) == datetime(2026, 7, 31, 12, 31)


def test_hora_local_retorna_naive():
    dt = datetime(2026, 7, 31, 15, 31, tzinfo=timezone.utc)
    assert hora_local(dt).tzinfo is None


def test_hora_local_none():
    assert hora_local(None) is None


def test_utcnow_eh_aware():
    assert utcnow().tzinfo is not None


def test_hoje_inicio_utc_equivale_a_meia_noite_local():
    inicio = hora_local(hoje_inicio_utc())
    agora = hora_local(utcnow())
    assert (inicio.hour, inicio.minute, inicio.second) == (0, 0, 0)
    assert inicio.date() == agora.date()


def test_inicio_mes_utc_equivale_ao_primeiro_dia_local():
    inicio = hora_local(inicio_mes_utc())
    agora = hora_local(utcnow())
    assert inicio.day == 1
    assert inicio.month == agora.month
    assert (inicio.hour, inicio.minute, inicio.second) == (0, 0, 0)


def test_intervalo_dia_local_para_utc():
    inicio, fim = intervalo_dia_local_para_utc('2026-07-31')
    esperado_inicio = datetime(2026, 7, 31, 3, 0, tzinfo=timezone.utc)
    assert inicio == esperado_inicio
    assert fim - inicio == timedelta(days=1)


def test_intervalo_dia_local_para_utc_retorna_aware():
    inicio, _ = intervalo_dia_local_para_utc('2026-07-31')
    assert inicio.tzinfo is not None