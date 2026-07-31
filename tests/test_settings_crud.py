from conftest import csrf_token, meta_csrf, login, criar_tecnico, criar_usuario_comum
from database.models.usuarios import Setor, Cargo
from database.models.credencial import Credencial


def test_settings_hub_admin(client):
    login(client)
    resp = client.get('/settings/')
    assert resp.status_code == 200


def test_settings_hub_usuario_bloqueado(client):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/settings/')
    assert resp.status_code in (302, 403)


def test_settings_hub_tecnico_bloqueado(client):
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/settings/')
    assert resp.status_code in (302, 403)


# ── SETORES ─────────────────────────────────────────────

def test_lista_setores(client):
    login(client)
    resp = client.get('/settings/setor/')
    assert resp.status_code == 200
    assert b'TI' in resp.data


def test_form_criar_setor(client):
    login(client)
    resp = client.get('/settings/setor/new')
    assert resp.status_code == 200


def test_criar_setor(client):
    login(client)
    token = meta_csrf(client)
    resp = client.post('/settings/setor/', data={
        'nome': 'RH', 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Setor.select().where(Setor.nome == 'RH').count() == 1


def test_criar_setor_duplicado(client):
    login(client)
    token = meta_csrf(client)
    client.post('/settings/setor/', data={'nome': 'RH', 'csrf_token': token}, follow_redirects=True)
    token = meta_csrf(client)
    resp = client.post('/settings/setor/', data={'nome': 'RH', 'csrf_token': token}, follow_redirects=True)
    assert resp.status_code == 200
    assert Setor.select().where(Setor.nome == 'RH').count() == 1


def test_editar_setor(client):
    login(client)
    Setor.create(nome='RH')
    resp = client.get('/settings/setor/2/edit')
    assert resp.status_code == 200


def test_atualizar_setor(client):
    login(client)
    Setor.create(nome='RH')
    token = meta_csrf(client)
    resp = client.post('/settings/setor/2/update', data={
        'nome': 'Recursos Humanos', 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Setor.get_by_id(2).nome == 'Recursos Humanos'


def test_deletar_setor(client):
    login(client)
    Setor.create(nome='RH')
    token = meta_csrf(client)
    resp = client.delete('/settings/setor/2/delete',
                         headers={'X-CSRFToken': token})
    assert resp.status_code == 200
    assert resp.get_json() == {'deleted': 'ok'}
    assert Setor.select().where(Setor.nome == 'RH').count() == 0


def test_setor_nao_autenticado(client):
    resp = client.get('/settings/setor/')
    assert resp.status_code == 302


# ── CARGOS ──────────────────────────────────────────────

def test_lista_cargos(client):
    login(client)
    resp = client.get('/settings/cargo/')
    assert resp.status_code == 200
    assert 'Técnico(a) de TI'.encode() in resp.data


def test_form_criar_cargo(client):
    login(client)
    resp = client.get('/settings/cargo/new')
    assert resp.status_code == 200


def test_criar_cargo(client):
    login(client)
    token = meta_csrf(client)
    setor = Setor.select().first()
    resp = client.post('/settings/cargo/', data={
        'nome': 'Analista', 'setor_id': str(setor.id), 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Cargo.select().where(Cargo.nome == 'Analista').count() == 1


def test_editar_cargo(client):
    login(client)
    setor = Setor.select().first()
    Cargo.create(nome='Analista', setor=setor)
    resp = client.get('/settings/cargo/2/edit')
    assert resp.status_code == 200


def test_atualizar_cargo(client):
    login(client)
    setor = Setor.select().first()
    Cargo.create(nome='Analista', setor=setor)
    token = meta_csrf(client)
    resp = client.post('/settings/cargo/2/update', data={
        'nome': 'Analista Senior', 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Cargo.get_by_id(2).nome == 'Analista Senior'


def test_deletar_cargo(client):
    login(client)
    setor = Setor.select().first()
    Cargo.create(nome='Analista', setor=setor)
    token = meta_csrf(client)
    resp = client.delete('/settings/cargo/2/delete',
                         headers={'X-CSRFToken': token})
    assert resp.status_code == 200
    assert resp.get_json() == {'deleted': 'ok'}
    assert Cargo.select().where(Cargo.nome == 'Analista').count() == 0


# ── CREDENCIAIS ─────────────────────────────────────────

def test_lista_credenciais(client):
    login(client)
    resp = client.get('/settings/credencial/')
    assert resp.status_code == 200


def test_form_criar_credencial(client):
    login(client)
    resp = client.get('/settings/credencial/new')
    assert resp.status_code == 200


def test_criar_credencial(client):
    login(client)
    token = meta_csrf(client)
    resp = client.post('/settings/credencial/', data={
        'titulo': 'AWS Root', 'username': 'admin',
        'senha': 's3nh4F0rt3', 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Credencial.select().count() == 1
    c = Credencial.select().first()
    assert c.titulo == 'AWS Root'
    assert c.username == 'admin'


def test_criar_credencial_sem_campos_obrigatorios(client):
    login(client)
    token = meta_csrf(client)
    resp = client.post('/settings/credencial/', data={
        'titulo': '', 'username': '', 'senha': '', 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Credencial.select().count() == 0


def test_editar_credencial(client):
    login(client)
    Credencial.create(titulo='AWS', username='admin', senha='enc', created_by=1)
    resp = client.get('/settings/credencial/1/edit')
    assert resp.status_code == 200


def test_atualizar_credencial(client):
    login(client)
    Credencial.create(titulo='AWS', username='admin', senha='enc', created_by=1)
    token = meta_csrf(client)
    resp = client.post('/settings/credencial/1/update', data={
        'titulo': 'AWS Updated', 'username': 'root',
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Credencial.get_by_id(1).titulo == 'AWS Updated'


def test_revelar_senha(client):
    login(client)
    from utils.crypto import encrypt
    import os
    secret = os.environ.get('SECRET_KEY')
    Credencial.create(
        titulo='AWS', username='admin',
        senha=encrypt('minha-senha', secret), created_by=1
    )
    token = meta_csrf(client)
    resp = client.post('/settings/credencial/1/reveal',
                       headers={'X-CSRFToken': token})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['senha'] == 'minha-senha'


def test_deletar_credencial(client):
    login(client)
    Credencial.create(titulo='AWS', username='admin', senha='enc', created_by=1)
    token = meta_csrf(client)
    resp = client.delete('/settings/credencial/1/delete',
                         headers={'X-CSRFToken': token})
    assert resp.status_code == 200
    assert resp.get_json() == {'deleted': 'ok'}
    assert Credencial.select().count() == 0


def test_credencial_nao_autenticado(client):
    resp = client.get('/settings/credencial/')
    assert resp.status_code == 302