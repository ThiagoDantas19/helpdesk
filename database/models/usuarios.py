from peewee import Model, AutoField, CharField, BooleanField, DateField, ForeignKeyField, TextField
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import db
from utils.constants import TipoVinculo

class Setor(Model):
    id = AutoField()
    nome = CharField(unique=True)

    class Meta:
        database = db

class Cargo(Model):
    id = AutoField()
    nome = CharField()
    setor = ForeignKeyField(Setor, backref='cargos', on_delete='CASCADE')

    class Meta:
        database = db

class User(UserMixin, Model):
    id = AutoField()
    nome_completo = CharField()
    email = CharField(unique=True, null=True)
    telefone = CharField(null=True)

    setor = ForeignKeyField(Setor, backref='usuarios')
    cargo = ForeignKeyField(Cargo, backref='usuarios')

    ativo = BooleanField(default=True)
    tipo_acesso = CharField(default='usuario')
    tipo_vinculo = CharField(default=TipoVinculo.EFETIVO.value)
    username = CharField(unique=True, null=True)
    password_hash = CharField(null=True)

    data_admissao = DateField(null=True)
    acesso_ad = BooleanField(default=False)
    acesso_sistema = BooleanField(default=False)
    acesso_sharepoint = BooleanField(default=False)
    biometria_dedo = BooleanField(default=False)
    biometria_facial = BooleanField(default=False)
    perfil_intelbras = CharField(null=True)
    email_corporativo = CharField(null=True)

    observacoes = TextField(null=True)
    data_desligamento = DateField(null=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.ativo

    def get_id(self):
        return str(self.id)

    class Meta:
        database = db