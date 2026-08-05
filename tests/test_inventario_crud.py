import pytest
from conftest import csrf_token, meta_csrf, login, criar_tecnico, criar_usuario_comum
from database.models.equipamentos import Patrimonio, Computador, Celular, TelefoneIP, Impressora, ItemDiverso, Auditoria, criar_auditoria
from database.models.usuarios import Setor


TYPES = [
    pytest.param('computador', 'computador', {
        'codigo_etiqueta': '0001', 'nome_identificador': 'PC-Admin',
        'tag': 'TAG-001', 'nome_ad': 'ADMIN-PC', 'numero_serie': 'SN-001'
    }, Computador),
    pytest.param('celular', 'celular', {
        'patrimonio': '0002', 'modelo': 'iPhone 12',
        'numero_serie': 'SN-CL-001', 'email_vinculado': 'test@test.com',
        'senha_google': 'gmail123', 'senha_icloud': 'icloud456'
    }, Celular),
    pytest.param('telefone', 'telefone', {
        'patrimonio': '0003', 'ramal': '101',
        'modelo': 'Cisco 7841', 'tag': 'TAG-TL-001'
    }, TelefoneIP),
    pytest.param('impressora', 'impressora', {
        'patrimonio': '0004', 'marca': 'HP',
        'modelo': 'LaserJet', 'numero_serie': 'SN-IM-001'
    }, Impressora),
    pytest.param('item_diverso', 'item', {
        'patrimonio': '0005', 'nome': 'Mouse',
        'tipo_item': 'Periférico'
    }, ItemDiverso),
]


COMPUTADOR_SPEC = {
    'hardware_integro': True, 'bateria_ok': True, 'perifericos_ok': True,
    'limpeza_fisica_ok': True, 'antivirus_ok': True, 'criptografia_ok': True,
    'updates_ok': True, 'softwares_ok': True, 'dominio_ok': True,
    'vpn_ok': True, 'limpeza_disco_ok': True, 'alocacao_ok': True, 'etiqueta_legivel': True,
}


def _criar_equipamento(client, tipo, url_prefix, form_data):
    login(client)
    token = meta_csrf(client)
    setor = Setor.select().first()
    data = {**form_data, 'setor_id': str(setor.id), 'csrf_token': token}
    resp = client.post(f'/inventario/{url_prefix}/', data=data, follow_redirects=True)
    return resp


def _criar_auditoria_valida(pat):
    spec = {}
    if pat.tipo == 'computador':
        spec = COMPUTADOR_SPEC
    elif pat.tipo == 'celular':
        spec = {'apps_ok': True, 'fotos_ok': True, 'informacoes_ok': True, 'whatsapp_ok': True, 'avarias_ok': True}
    elif pat.tipo == 'telefone':
        spec = {'chamada_ok': True, 'fone_ok': True, 'cabo_rede_ok': True, 'poe_ok': True, 'etiqueta_legivel': True}
    elif pat.tipo == 'impressora':
        spec = {'liga_ok': True, 'qualidade_impressao_ok': True, 'scanner_ok': True, 'nivel_suprimentos_ok': True, 'cabos_ok': True}
    elif pat.tipo == 'item_diverso':
        spec = {'estado_fisico_ok': True, 'funcionamento_ok': True, 'acessorios_ok': True, 'etiqueta_legivel': True}
    return criar_auditoria(pat, {'status_geral_ok': True, 'observacoes': 'teste'}, spec, uploaded_by=1)


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_lista_equipamentos_tecnico(client, tipo, url_prefix, form_data, model_cls):
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get(f'/inventario/{url_prefix}/')
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_lista_equipamentos_usuario_bloqueado(client, tipo, url_prefix, form_data, model_cls):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get(f'/inventario/{url_prefix}/')
    assert resp.status_code in (302, 403)


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_form_criar_equipamento_admin(client, tipo, url_prefix, form_data, model_cls):
    login(client)
    resp = client.get(f'/inventario/{url_prefix}/new')
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_criar_equipamento(client, tipo, url_prefix, form_data, model_cls):
    resp = _criar_equipamento(client, tipo, url_prefix, form_data)
    assert resp.status_code == 200
    assert Patrimonio.select().count() == 1
    pat = Patrimonio.select().first()
    assert pat.tipo == tipo
    assert model_cls.select().count() == 1


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_detalhes_equipamento(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get(f'/inventario/{url_prefix}/{pat.id}')
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_form_editar_equipamento_admin(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    login(client)
    resp = client.get(f'/inventario/{url_prefix}/{pat.id}/edit')
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_atualizar_equipamento(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    login(client)
    token = meta_csrf(client)
    update_data = {**form_data, 'csrf_token': token, 'ativo': '1'}
    resp = client.post(f'/inventario/{url_prefix}/{pat.id}/update', data=update_data, follow_redirects=True)
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_form_auditoria(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get(f'/inventario/{url_prefix}/{pat.id}/auditar')
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_realizar_auditoria(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    login(client)
    token = meta_csrf(client)
    resp = client.post(f'/inventario/{url_prefix}/{pat.id}/auditar', data={
        'csrf_token': token, 'observacoes': 'Tudo ok'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Auditoria.select().count() == 1


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_historico_auditorias(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get(f'/inventario/{url_prefix}/{pat.id}/auditorias')
    assert resp.status_code == 200


@pytest.mark.parametrize('tipo,url_prefix,form_data,model_cls', TYPES)
def test_export_auditorias_csv(client, tipo, url_prefix, form_data, model_cls):
    _criar_equipamento(client, tipo, url_prefix, form_data)
    pat = Patrimonio.select().first()
    _criar_auditoria_valida(pat)
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get(f'/inventario/{url_prefix}/{pat.id}/auditorias/export')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'


def test_hub_inventario_tecnico(client):
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/')
    assert resp.status_code == 200


def test_hub_inventario_usuario_bloqueado(client):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/inventario/')
    assert resp.status_code in (302, 403)


def test_hub_inventario_nao_autenticado(client):
    resp = client.get('/inventario/')
    assert resp.status_code == 302


def test_lista_celular_marca_auditoria_do_mes(client):
    from datetime import timedelta
    from utils.time import utcnow

    login(client)
    setor = Setor.select().first()

    pat_mes = Patrimonio.create(codigo_etiqueta='0101', nome_identificador='Cel Mes', tipo='celular', setor=setor, ativo=True)
    Celular.create(patrimonio=pat_mes, modelo='Android')
    pat_passado = Patrimonio.create(codigo_etiqueta='0102', nome_identificador='Cel Antigo', tipo='celular', setor=setor, ativo=True)
    Celular.create(patrimonio=pat_passado, modelo='Android Antigo')

    spec = {'apps_ok': True, 'fotos_ok': True, 'informacoes_ok': True, 'whatsapp_ok': True, 'avarias_ok': True}
    criar_auditoria(pat_mes, {'status_geral_ok': True, 'observacoes': 'mes atual'}, spec, uploaded_by=1)
    a = criar_auditoria(pat_passado, {'status_geral_ok': True, 'observacoes': 'mes passado'}, spec, uploaded_by=1)
    Auditoria.update(data_auditoria=utcnow() - timedelta(days=35)).where(Auditoria.id == a.id).execute()

    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/celular/')
    assert resp.status_code == 200
    corpo = resp.data.decode('utf-8')
    linha_mes = corpo[corpo.index('0101'):corpo.index('0101') + 1800]
    linha_antigo = corpo[corpo.index('0102'):corpo.index('0102') + 1800]
    assert 'Auditoria do mês concluída' in linha_mes
    assert 'Sem auditoria no mês' in linha_antigo