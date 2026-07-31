from conftest import csrf_token, login, criar_tecnico, criar_usuario_comum

def test_usuario_nao_ve_user_list(client):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/user/')
    assert resp.status_code == 302 or resp.status_code == 403

def test_tecnico_ve_inventario(client):
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/inventario/')
    assert resp.status_code == 200

def test_usuario_nao_ve_inventario(client):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/inventario/')
    assert resp.status_code == 302 or resp.status_code == 403

def test_admin_ve_logs(client):
    login(client)
    resp = client.get('/logs/')
    assert resp.status_code == 200

def test_tecnico_nao_ve_logs(client):
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/logs/')
    assert resp.status_code == 302 or resp.status_code == 403

def test_usuario_nao_ve_settings(client):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/settings/')
    assert resp.status_code == 302 or resp.status_code == 403

def test_unauthenticated_blocked_inventario(client):
    resp = client.get('/inventario/')
    assert resp.status_code == 302

def test_unauthenticated_blocked_logs(client):
    resp = client.get('/logs/')
    assert resp.status_code == 302

def test_unauthenticated_blocked_user_list(client):
    resp = client.get('/user/')
    assert resp.status_code == 302

def test_admin_pode_criar_usuario(client):
    login(client)
    resp = client.get('/user/new')
    assert resp.status_code == 200
