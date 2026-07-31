import csv
from io import StringIO
from conftest import login, criar_tecnico, criar_usuario_comum
from database.models.equipamentos import (
    Patrimonio, Computador, Celular, TelefoneIP, Impressora, ItemDiverso,
    Auditoria, criar_auditoria
)
from database.models.usuarios import Setor


COMPUTADOR_SPEC = {
    'hardware_integro': True, 'bateria_ok': True, 'perifericos_ok': True,
    'limpeza_fisica_ok': True, 'antivirus_ok': True, 'criptografia_ok': True,
    'updates_ok': True, 'softwares_ok': True, 'dominio_ok': True,
    'vpn_ok': True, 'limpeza_disco_ok': True, 'alocacao_ok': True, 'etiqueta_legivel': True,
}

CELULAR_SPEC = {'apps_ok': True, 'fotos_ok': True, 'informacoes_ok': True, 'whatsapp_ok': True, 'avarias_ok': True}
TELEFONE_SPEC = {'chamada_ok': True, 'fone_ok': True, 'cabo_rede_ok': True, 'poe_ok': True, 'etiqueta_legivel': True}
IMPRESSORA_SPEC = {'liga_ok': True, 'qualidade_impressao_ok': True, 'scanner_ok': True, 'nivel_suprimentos_ok': True, 'cabos_ok': True}
ITEM_SPEC = {'estado_fisico_ok': True, 'funcionamento_ok': True, 'acessorios_ok': True, 'etiqueta_legivel': True}


def _criar_patrimonio_computador():
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='PC-EXP-001', nome_identificador='PC-Export',
        tipo='computador', setor=setor, ativo=True
    )
    Computador.create(patrimonio=pat, tag='TAG-EXP')
    return pat


def _criar_patrimonio_celular():
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='CL-EXP-001', nome_identificador='Celular Export',
        tipo='celular', setor=setor, ativo=True
    )
    Celular.create(patrimonio=pat, modelo='iPhone 12')
    return pat


def _criar_patrimonio_telefone():
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='TL-EXP-001', nome_identificador='Ramal 101',
        tipo='telefone', setor=setor, ativo=True
    )
    TelefoneIP.create(patrimonio=pat, ramal='101', modelo='Cisco')
    return pat


def _criar_patrimonio_impressora():
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='IM-EXP-001', nome_identificador='HP LaserJet',
        tipo='impressora', setor=setor, ativo=True
    )
    Impressora.create(patrimonio=pat, marca='HP', modelo='LaserJet')
    return pat


def _criar_patrimonio_item():
    setor = Setor.select().first()
    pat = Patrimonio.create(
        codigo_etiqueta='IT-EXP-001', nome_identificador='Mouse Gamer',
        tipo='item_diverso', setor=setor, ativo=True
    )
    ItemDiverso.create(patrimonio=pat, nome='Mouse Gamer', tipo_item='Periférico')
    return pat


def test_export_csv_computador_contem_cabecalho_e_dados(client):
    login(client)
    pat = _criar_patrimonio_computador()
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Audit OK'}, COMPUTADOR_SPEC, uploaded_by=1)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/computador/1/auditorias/export')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 2
    assert 'Hardware' in rows[0]
    assert 'Audit OK' in rows[1][-1]


def test_export_csv_celular_contem_cabecalho_e_dados(client):
    login(client)
    pat = _criar_patrimonio_celular()
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Celular OK'}, CELULAR_SPEC, uploaded_by=1)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/celular/1/auditorias/export')
    assert resp.status_code == 200
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 2
    assert 'Apps' in rows[0]
    assert 'Celular OK' in rows[1][-1]


def test_export_csv_telefone_contem_cabecalho_e_dados(client):
    login(client)
    pat = _criar_patrimonio_telefone()
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Ramal OK'}, TELEFONE_SPEC, uploaded_by=1)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/telefone/1/auditorias/export')
    assert resp.status_code == 200
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 2
    assert 'Chamada' in rows[0]
    assert 'Ramal OK' in rows[1][-1]


def test_export_csv_impressora_contem_cabecalho_e_dados(client):
    login(client)
    pat = _criar_patrimonio_impressora()
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Impressora OK'}, IMPRESSORA_SPEC, uploaded_by=1)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/impressora/1/auditorias/export')
    assert resp.status_code == 200
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 2
    assert 'Liga' in rows[0]
    assert 'Impressora OK' in rows[1][-1]


def test_export_csv_item_contem_cabecalho_e_dados(client):
    login(client)
    pat = _criar_patrimonio_item()
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Item OK'}, ITEM_SPEC, uploaded_by=1)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/item/1/auditorias/export')
    assert resp.status_code == 200
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 2
    assert 'Estado Fisico' in rows[0]
    assert 'Item OK' in rows[1][-1]


def test_export_csv_multiplas_auditorias(client):
    login(client)
    pat = _criar_patrimonio_computador()
    criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'Primeira'}, COMPUTADOR_SPEC, uploaded_by=1)
    criar_auditoria(pat, {'status_geral_ok': False, 'observacoes': 'Segunda'}, {k: False for k in COMPUTADOR_SPEC}, uploaded_by=1)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/computador/1/auditorias/export')
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 3
    assert rows[1][-1] == 'Segunda'
    assert rows[2][-1] == 'Primeira'


def test_export_sem_auditorias_retorna_csv_com_cabecalho(client):
    login(client)
    _criar_patrimonio_computador()
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/computador/1/auditorias/export')
    assert resp.status_code == 200
    content = resp.data.decode('utf-8')
    reader = csv.reader(StringIO(content))
    rows = list(reader)
    assert len(rows) == 1


def test_export_nao_autenticado(client):
    _criar_patrimonio_computador()
    resp = client.get('/inventario/computador/1/auditorias/export')
    assert resp.status_code == 302


def test_export_usuario_bloqueado(client):
    _criar_patrimonio_computador()
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/inventario/computador/1/auditorias/export')
    assert resp.status_code in (302, 403)


def test_export_csv_filename_contem_etiqueta(client):
    login(client)
    _criar_patrimonio_computador()
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/computador/1/auditorias/export')
    assert resp.status_code == 200
    assert 'PC-EXP-001' in resp.headers.get('Content-disposition', '')