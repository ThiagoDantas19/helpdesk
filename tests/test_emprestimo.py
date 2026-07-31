from tests.conftest import login, criar_tecnico, criar_usuario_comum, meta_csrf
from database.models.equipamentos import Patrimonio, Computador, ItemDiverso
from database.models.usuarios import User, Setor, Cargo
from database.models.emprestimo import Emprestimo


def _criar_computador():
    setor = Setor.get()
    pat = Patrimonio.create(
        nome_identificador='Notebook Teste', tipo='computador', setor=setor
    )
    Computador.create(patrimonio=pat, tag='SN001')
    return pat


def _criar_item(nome='Item Teste'):
    setor = Setor.get()
    pat = Patrimonio.create(
        nome_identificador=nome, tipo='item_diverso', setor=setor
    )
    ItemDiverso.create(patrimonio=pat, nome=nome, tipo_item='periferico')
    return pat


def _criar_usuario(nome, username):
    setor = Setor.get()
    cargo = Cargo.get()
    return User.create(
        nome_completo=nome, email=f'{username}@local',
        username=username, tipo_acesso='usuario',
        setor=setor, cargo=cargo, ativo=True
    )


def test_lista_emprestimos_admin(client):
    login(client)
    resp = client.get('/emprestimo/')
    assert resp.status_code == 200


def test_lista_emprestimos_tecnico(client):
    criar_tecnico()
    login(client, 'tecnico', 'tecnico')
    resp = client.get('/emprestimo/')
    assert resp.status_code == 200


def test_lista_emprestimos_usuario_bloqueado(client):
    criar_usuario_comum()
    login(client, 'usuario', 'usuario')
    resp = client.get('/emprestimo/')
    assert resp.status_code == 403


def test_form_novo_emprestimo_admin(client):
    login(client)
    resp = client.get('/emprestimo/new')
    assert resp.status_code == 200
    assert b'Novo Empr' in resp.data


def test_criar_emprestimo(client):
    login(client)
    token = meta_csrf(client)
    user = _criar_usuario('Teste', 'teste')
    pat = _criar_computador()
    resp = client.post('/emprestimo/', data={
        'patrimonio_id': pat.id, 'usuario_id': user.id,
        'observacoes': 'Teste de empréstimo', 'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200


def test_detalhes_emprestimo(client):
    login(client)
    admin = User.get()
    user = _criar_usuario('Teste', 'teste2')
    pat = _criar_item('Fone Teste')
    emp = Emprestimo.create(
        patrimonio=pat, usuario=user, responsavel=admin,
        observacoes='Detalhes'
    )
    resp = client.get(f'/emprestimo/{emp.id}')
    assert resp.status_code == 200
    assert b'Fone Teste' in resp.data


def test_devolver_emprestimo(client):
    login(client)
    token = meta_csrf(client)
    admin = User.get()
    user = _criar_usuario('Teste', 'teste3')
    pat = _criar_item('Hub Teste')
    emp = Emprestimo.create(patrimonio=pat, usuario=user, responsavel=admin)
    assert emp.data_devolucao is None
    resp = client.post(f'/emprestimo/{emp.id}/devolver', data={
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Emprestimo.get_by_id(emp.id).data_devolucao is not None


def test_deletar_emprestimo(client):
    login(client)
    token = meta_csrf(client)
    admin = User.get()
    user = _criar_usuario('Teste', 'teste4')
    pat = _criar_item('Mic Teste')
    emp = Emprestimo.create(patrimonio=pat, usuario=user, responsavel=admin)
    resp = client.post(f'/emprestimo/{emp.id}/delete', data={
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert Emprestimo.select().where(Emprestimo.id == emp.id).count() == 0
