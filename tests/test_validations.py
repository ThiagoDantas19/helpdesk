import re


def _csrf_token(client):
    resp = client.get('/login')
    m = re.search(rb'name="csrf_token".*?value="([^"]+)"', resp.data)
    return m.group(1).decode() if m else ''


def _login(client, username='admin', password='admin'):
    token = _csrf_token(client)
    resp = client.post('/login', data={
        'username': username,
        'password': password,
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200, f'Login failed for {username}: {resp.status_code}'
    return resp


def test_login_page_loads(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_login_success(client):
    _login(client)


def test_login_invalid(client):
    token = _csrf_token(client)
    resp = client.post('/login', data={
        'username': 'admin',
        'password': 'wrong',
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'inv' in resp.data.lower() or b'erro' in resp.data.lower()


def test_logout(client):
    _login(client)
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200


def test_unauthenticated_redirect(client):
    resp = client.get('/')
    assert resp.status_code == 302


def test_admin_access_user_list(client):
    _login(client)
    resp = client.get('/user/')
    assert resp.status_code == 200
