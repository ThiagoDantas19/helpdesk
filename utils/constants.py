import os
from enum import Enum


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')


class TipoEquipamento(str, Enum):
    COMPUTADOR = 'computador'
    CELULAR = 'celular'
    TELEFONE = 'telefone'
    IMPRESSORA = 'impressora'
    ITEM_DIVERSO = 'item_diverso'

    def url_name(self):
        if self == self.ITEM_DIVERSO:
            return 'item'
        return self.value

    @classmethod
    def list(cls):
        return [t.value for t in cls]


class StatusChamado(str, Enum):
    ABERTO = 'aberto'
    EM_ANDAMENTO = 'em_andamento'
    FECHADO = 'fechado'


class PrioridadeChamado(str, Enum):
    BAIXA = 'baixa'
    MEDIA = 'media'
    ALTA = 'alta'
    URGENTE = 'urgente'


class TipoVinculo(str, Enum):
    EFETIVO = 'efetivo'
    FREELANCER = 'freelancer'
    TERCEIRIZADO = 'terceirizado'
    ESTAGIARIO = 'estagiario'


class TipoAcesso(str, Enum):
    USUARIO = 'usuario'
    TECNICO = 'tecnico'
    ADMIN = 'admin'


TIPO_COMPUTADOR = TipoEquipamento.COMPUTADOR.value
TIPO_CELULAR = TipoEquipamento.CELULAR.value
TIPO_TELEFONE = TipoEquipamento.TELEFONE.value
TIPO_IMPRESSORA = TipoEquipamento.IMPRESSORA.value
TIPO_ITEM_DIVERSO = TipoEquipamento.ITEM_DIVERSO.value

TIPOS_INVENTARIO = TipoEquipamento.list()
