from peewee import Model, AutoField, ForeignKeyField, DateTimeField, DateField, TextField
from database.database import db
from database.models.usuarios import User
from database.models.equipamentos import Patrimonio
from utils.time import utcnow


class Emprestimo(Model):
    id = AutoField()
    patrimonio = ForeignKeyField(Patrimonio, backref='emprestimos', on_delete='CASCADE')
    usuario = ForeignKeyField(User, backref='emprestimos_recebidos')
    responsavel = ForeignKeyField(User, backref='emprestimos_realizados')
    data_emprestimo = DateTimeField(default=utcnow)
    data_devolucao_prevista = DateField(null=True)
    data_devolucao = DateTimeField(null=True)
    observacoes = TextField(null=True)
    observacoes_devolucao = TextField(null=True)

    class Meta:
        database = db
