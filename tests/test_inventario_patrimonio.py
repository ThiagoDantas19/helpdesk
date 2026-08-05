import pytest
from conftest import meta_csrf, login
from database.models.equipamentos import Patrimonio, Computador
from database.models.usuarios import Setor


def _login_admin(client):
    login(client)
    return meta_csrf(client)


def _criar_computador(client, token, codigo='0001', nome='PC-Teste'):
    setor = Setor.select().first()
    return client.post('/inventario/computador/', data={
        'codigo_etiqueta': codigo,
        'nome_identificador': nome,
        'tag': 'TAG-1',
        'data_fabricacao': '',
        'setor_id': str(setor.id),
        'csrf_token': token,
    }, follow_redirects=True)


def test_verificar_patrimonio_disponivel(client):
    token = _login_admin(client)
    resp = client.get('/inventario/patrimonio/verificar?codigo=9999')
    assert resp.status_code == 200
    assert resp.get_json() == {'disponivel': True, 'identificacao': ''}


def test_verificar_patrimonio_sem_codigo(client):
    _login_admin(client)
    resp = client.get('/inventario/patrimonio/verificar?codigo=')
    assert resp.get_json()['disponivel'] is True


def test_verificar_patrimonio_duplicado(client):
    token = _login_admin(client)
    _criar_computador(client, token, '0001', 'PC-Teste')
    resp = client.get('/inventario/patrimonio/verificar?codigo=0001')
    data = resp.get_json()
    assert data['disponivel'] is False
    assert 'PC-Teste' in data['identificacao']


def test_verificar_patrimonio_exclui_proprio_na_edicao(client):
    token = _login_admin(client)
    _criar_computador(client, token, '0001', 'PC-Teste')
    pat = Patrimonio.select().first()
    resp = client.get(f'/inventario/patrimonio/verificar?codigo=0001&excluir={pat.id}')
    assert resp.get_json()['disponivel'] is True


def test_verificar_patrimonio_nao_autenticado(client):
    resp = client.get('/inventario/patrimonio/verificar?codigo=0001')
    assert resp.status_code in (302,)


def test_criar_patrimonio_duplicado_preserva_formulario(client):
    token = _login_admin(client)
    _criar_computador(client, token, '0001', 'PC-Existente')
    setor = Setor.select().first()
    resp = client.post('/inventario/computador/', data={
        'codigo_etiqueta': '0001',
        'nome_identificador': 'PC-Novo-Nome',
        'tag': 'TAG-2',
        'data_fabricacao': '',
        'setor_id': str(setor.id),
        'csrf_token': token,
    })
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'já está cadastrado' in body
    assert 'window.__dadosForm' in body
    assert 'PC-Novo-Nome' in json_body(body)
    assert Patrimonio.select().count() == 1
    assert Computador.select().count() == 1


def test_editar_patrimonio_duplicado_preserva_formulario(client):
    token = _login_admin(client)
    _criar_computador(client, token, '0001', 'PC-Um')
    _criar_computador(client, token, '0002', 'PC-Dois')
    pat2 = Patrimonio.select().where(Patrimonio.codigo_etiqueta == '0002').get()
    resp = client.post(f'/inventario/computador/{pat2.id}/update', data={
        'codigo_etiqueta': '0001',
        'nome_identificador': 'PC-Dois-Renomeado',
        'tag': 'TAG-2',
        'data_fabricacao': '',
        'setor_id': str(Setor.select().first().id),
        'ativo': '1',
        'csrf_token': token,
    })
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'já está cadastrado' in body
    assert 'window.__dadosForm' in body
    assert 'PC-Dois-Renomeado' in json_body(body)
    pat2 = Patrimonio.select().where(Patrimonio.codigo_etiqueta == '0002').get()
    assert pat2 is not None
    assert Patrimonio.select().count() == 2


def test_editar_mantendo_proprio_patrimonio_ok(client):
    token = _login_admin(client)
    _criar_computador(client, token, '0001', 'PC-Um')
    pat = Patrimonio.select().first()
    resp = client.post(f'/inventario/computador/{pat.id}/update', data={
        'codigo_etiqueta': '0001',
        'nome_identificador': 'PC-Um-Editado',
        'tag': 'TAG-1',
        'data_fabricacao': '',
        'setor_id': str(Setor.select().first().id),
        'ativo': '1',
        'csrf_token': token,
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert 'já está cadastrado' not in resp.get_data(as_text=True)
    pat = Patrimonio.select().where(Patrimonio.id == pat.id).get()
    assert pat.nome_identificador == 'PC-Um-Editado'


def json_body(body):
    start = body.find('window.__dadosForm = ')
    assert start != -1
    sub = body[start:]
    inicio_json = sub.find('{')
    fim_json = sub.find('};')
    return sub[inicio_json:fim_json + 1]