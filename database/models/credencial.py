from peewee import Model, AutoField, CharField, TextField, DateTimeField, ForeignKeyField
from database.database import db
from database.models.usuarios import User
from utils.time import utcnow


class Credencial(Model):
    id = AutoField()
    titulo = CharField()
    url = CharField(null=True)
    username = CharField()
    senha = TextField()
    observacao = TextField(null=True)
    created_by = ForeignKeyField(User, null=True, on_delete='SET NULL')
    created_at = DateTimeField(default=utcnow)
    updated_at = DateTimeField(null=True)

    class Meta:
        database = db
        indexes = (
            (('titulo',), False),
        )
