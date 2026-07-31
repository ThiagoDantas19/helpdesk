from peewee import Model, AutoField, CharField, BooleanField, DateTimeField, DateField, ForeignKeyField
from database.database import db
from database.models.usuarios import User
from utils.time import utcnow


class Tarefa(Model):
    id = AutoField()
    usuario = ForeignKeyField(User, backref='tarefas', on_delete='CASCADE')
    titulo = CharField()
    concluida = BooleanField(default=False)
    data_vencimento = DateField(null=True)
    criado_em = DateTimeField(default=utcnow)

    class Meta:
        database = db
        indexes = (
            (('usuario', 'concluida'), False),
        )
