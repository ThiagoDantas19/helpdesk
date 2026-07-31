from peewee import Model, AutoField, CharField, TextField, DateTimeField, ForeignKeyField, IntegerField
from database.database import db
from database.models.usuarios import User
from utils.time import utcnow


class Chamado(Model):
    id = AutoField()
    titulo = CharField()
    descricao = TextField()
    status = CharField(default='aberto')
    prioridade = CharField(default='media')
    categoria = CharField(null=True)
    resposta = TextField(null=True)
    nota_interna = TextField(null=True)
    funcionario = ForeignKeyField(User, backref='chamados')
    operador = ForeignKeyField(User, backref='chamados_operador', null=True, on_delete='SET NULL')
    criado_em = DateTimeField(default=utcnow)
    atualizado_em = DateTimeField(null=True)
    fechado_em = DateTimeField(null=True)

    class Meta:
        database = db
        indexes = (
            (('status', 'criado_em'), False),
            (('funcionario', 'criado_em'), False),
        )


class ChamadoEquipamento(Model):
    id = AutoField()
    chamado = ForeignKeyField(Chamado, backref='equipamentos', on_delete='CASCADE')
    tipo_equipamento = CharField()
    equipamento_id = IntegerField()

    class Meta:
        database = db
        indexes = (
            (('chamado', 'tipo_equipamento'), False),
            (('equipamento_id',), False),
        )


class ChamadoAnexo(Model):
    id = AutoField()
    chamado = ForeignKeyField(Chamado, backref='anexos', on_delete='CASCADE')
    filename = CharField()
    stored_filename = CharField()
    mimetype = CharField()
    filesize = IntegerField()
    uploaded_by = ForeignKeyField(User, null=True, on_delete='SET NULL')
    criado_em = DateTimeField(default=utcnow)

    class Meta:
        database = db
