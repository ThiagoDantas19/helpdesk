import re

def _login_get_csrf(client, username='admin', password='admin'):
    resp = client.get('/login')
    m = re.search(rb'name="csrf_token".*?value="([^"]+)"', resp.data)
    token = m.group(1).decode() if m else ''
    resp = client.post('/login', data={
        'username': username,
        'password': password,
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200, f'Login failed: {resp.status_code}'
    resp = client.get('/')
    m = re.search(rb'name="csrf-token" content="([^"]+)"', resp.data)
    return m.group(1).decode() if m else ''


def test_criar_tarefa(client):
    csrf = _login_get_csrf(client)
    resp = client.post('/api/tarefas',
        data='{"titulo": "Minha tarefa"}',
        content_type='application/json',
        headers={'X-CSRFToken': csrf})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['titulo'] == 'Minha tarefa'
    assert data['concluida'] == False


def test_criar_tarefa_sem_titulo(client):
    csrf = _login_get_csrf(client)
    resp = client.post('/api/tarefas',
        data='{"titulo": ""}',
        content_type='application/json',
        headers={'X-CSRFToken': csrf})
    assert resp.status_code == 400
    assert 'obrigat' in resp.get_json()['erro'].lower()


def test_listar_tarefas(client):
    csrf = _login_get_csrf(client)
    client.post('/api/tarefas',
        data='{"titulo": "Tarefa 1"}',
        content_type='application/json',
        headers={'X-CSRFToken': csrf})
    client.post('/api/tarefas',
        data='{"titulo": "Tarefa 2"}',
        content_type='application/json',
        headers={'X-CSRFToken': csrf})
    resp = client.get('/api/tarefas')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2


def test_toggle_tarefa(client):
    csrf = _login_get_csrf(client)
    resp = client.post('/api/tarefas',
        data='{"titulo": "Para alternar"}',
        content_type='application/json',
        headers={'X-CSRFToken': csrf})
    tarefa_id = resp.get_json()['id']
    resp = client.post(f'/api/tarefas/{tarefa_id}/toggle',
        headers={'X-CSRFToken': csrf})
    assert resp.status_code == 200
    assert resp.get_json()['concluida'] == True
    resp = client.post(f'/api/tarefas/{tarefa_id}/toggle',
        headers={'X-CSRFToken': csrf})
    assert resp.get_json()['concluida'] == False


def test_deletar_tarefa(client):
    csrf = _login_get_csrf(client)
    resp = client.post('/api/tarefas',
        data='{"titulo": "Para deletar"}',
        content_type='application/json',
        headers={'X-CSRFToken': csrf})
    tarefa_id = resp.get_json()['id']
    resp = client.delete(f'/api/tarefas/{tarefa_id}',
        headers={'X-CSRFToken': csrf})
    assert resp.status_code == 200
    resp = client.get('/api/tarefas')
    assert len(resp.get_json()) == 0


def test_csrf_ausente_rejeita(client):
    _login_get_csrf(client)
    resp = client.post('/api/tarefas',
        data='{"titulo": "Sem CSRF"}',
        content_type='application/json')
    assert resp.status_code == 400


def test_toggle_inexistente(client):
    csrf = _login_get_csrf(client)
    resp = client.post('/api/tarefas/999/toggle',
        headers={'X-CSRFToken': csrf})
    assert resp.status_code == 404


def test_deletar_inexistente(client):
    csrf = _login_get_csrf(client)
    resp = client.delete('/api/tarefas/999',
        headers={'X-CSRFToken': csrf})
    assert resp.status_code == 404


def test_calendario(client):
    _login_get_csrf(client)
    resp = client.get('/api/tarefas/calendario')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'semanas' in data
    assert 'dots' in data


def test_nao_autenticado_redireciona_api(client):
    resp = client.get('/api/tarefas')
    assert resp.status_code == 302
