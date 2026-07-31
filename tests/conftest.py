import os
import re
import pytest
from peewee import SqliteDatabase
from database.database import db
from database.models.usuarios import Setor, Cargo, User
from database.models.equipamentos import (
    Patrimonio, Computador, Celular, NumeroTelefone, TelefoneIP, Impressora, ItemDiverso,
    Auditoria, AuditoriaCelular, AuditoriaComputador, AuditoriaTelefone,
    AuditoriaImpressora, AuditoriaItemDiverso, AuditoriaAnexo, ItemAnexo
)
from database.models.chamados import Chamado, ChamadoEquipamento, ChamadoAnexo
from database.models.log import LogEntry
from database.models.tarefa import Tarefa
from database.models.credencial import Credencial
from database.models.emprestimo import Emprestimo

os.environ['SECRET_KEY'] = 'test-secret-key-not-for-production'

TABELAS = [
    Setor, Cargo, User,
    Patrimonio, Computador, Celular, NumeroTelefone, TelefoneIP, Impressora, ItemDiverso,
    Auditoria, AuditoriaCelular, AuditoriaComputador,
    AuditoriaTelefone, AuditoriaImpressora, AuditoriaItemDiverso,
    AuditoriaAnexo, ItemAnexo,
    Chamado, ChamadoEquipamento, ChamadoAnexo,
    LogEntry, Tarefa, Credencial, Emprestimo
]


@pytest.fixture(autouse=True)
def setup_db():
    mem_db = SqliteDatabase(':memory:')
    db.initialize(mem_db)
    db.connect()
    db.execute_sql('PRAGMA foreign_keys=ON')
    db.create_tables(TABELAS)
    _seed()
    yield
    db.close()


def _seed():
    setor = Setor.create(nome='TI')
    cargo = Cargo.create(nome='Técnico(a) de TI', setor=setor)
    admin = User.create(
        nome_completo='Administrador',
        email='admin@helpdesk.local',
        username='admin',
        tipo_acesso='admin',
        tipo_vinculo='efetivo',
        setor=setor,
        cargo=cargo,
        ativo=True
    )
    admin.set_password('admin')
    admin.save()


@pytest.fixture
def client(setup_db):
    from config import configure_all
    app = configure_all(skip_db_init=True)
    with app.test_client() as c:
        yield c


def csrf_token(client):
    resp = client.get('/login')
    m = re.search(rb'name="csrf_token".*?value="([^"]+)"', resp.data)
    return m.group(1).decode() if m else ''


def meta_csrf(client):
    resp = client.get('/')
    m = re.search(rb'name="csrf-token" content="([^"]+)"', resp.data)
    return m.group(1).decode() if m else ''


def logout(client):
    client.get('/logout', follow_redirects=True)


def login(client, username='admin', password='admin'):
    logout(client)
    token = csrf_token(client)
    resp = client.post('/login', data={
        'username': username,
        'password': password,
        'csrf_token': token
    }, follow_redirects=True)
    assert resp.status_code == 200, f'Login failed for {username}: {resp.status_code}'


def criar_tecnico():
    setor = Setor.get_or_none(Setor.nome == 'TI')
    if not setor:
        setor = Setor.create(nome='TI')
    cargo = Cargo.get_or_none(Cargo.nome == 'Técnico(a) de TI')
    if not cargo:
        cargo = Cargo.create(nome='Técnico(a) de TI', setor=setor)
    user = User.create(
        nome_completo='Tecnico Teste', email='tecnico@teste.local',
        username='tecnico', tipo_acesso='tecnico', setor=setor, cargo=cargo, ativo=True
    )
    user.set_password('tecnico')
    user.save()
    return user


def criar_usuario_comum():
    setor = Setor.get_or_none(Setor.nome == 'TI')
    if not setor:
        setor = Setor.create(nome='TI')
    cargo = Cargo.get_or_none(Cargo.nome == 'Técnico(a) de TI')
    if not cargo:
        cargo = Cargo.create(nome='Técnico(a) de TI', setor=setor)
    user = User.create(
        nome_completo='Usuario Comum', email='usuario@teste.local',
        username='usuario', tipo_acesso='usuario', setor=setor, cargo=cargo, ativo=True
    )
    user.set_password('usuario')
    user.save()
    return user
