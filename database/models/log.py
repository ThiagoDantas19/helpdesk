from peewee import Model, AutoField, CharField, TextField, DateTimeField, ForeignKeyField
from database.database import db
from database.models.usuarios import User
from utils.time import utcnow


class LogEntry(Model):
    id = AutoField()
    usuario = ForeignKeyField(User, null=True, on_delete='SET NULL')
    acao = CharField()
    entidade = CharField(null=True)
    entidade_id = CharField(null=True)
    descricao = TextField(null=True)
    ip = CharField(null=True)
    criado_em = DateTimeField(default=utcnow)

    class Meta:
        database = db
        indexes = (
            (('criado_em',), False),
            (('entidade', 'entidade_id'), False),
        )


def registrar_log(usuario, acao, entidade=None, entidade_id=None, descricao=None):
    from flask import request
    ip = request.remote_addr if request else None
    return LogEntry.create(
        usuario=usuario,
        acao=acao,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id else None,
        descricao=descricao,
        ip=ip
    )
