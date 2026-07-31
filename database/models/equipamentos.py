from peewee import Model, AutoField, CharField, BooleanField, DateField, TextField, DateTimeField, ForeignKeyField, IntegerField
from database.database import db
from database.models.usuarios import User, Setor
from utils.crypto import encrypt, decrypt
from utils.constants import TipoEquipamento
from utils.time import utcnow
from flask import current_app


class Patrimonio(Model):
    id = AutoField()
    codigo_etiqueta = CharField(max_length=4, unique=True, null=True)
    nome_identificador = CharField()
    tipo = CharField()
    setor = ForeignKeyField(Setor, backref='patrimonios', null=True, on_delete='SET NULL')
    responsavel = ForeignKeyField(User, backref='patrimonios', null=True, on_delete='SET NULL')
    ativo = BooleanField(default=True)
    observacoes = TextField(null=True)
    criado_em = DateTimeField(default=utcnow)

    class Meta:
        database = db
        indexes = (
            (('tipo', 'ativo'), False),
        )


class Computador(Model):
    patrimonio = ForeignKeyField(Patrimonio, primary_key=True, backref='detalhes_computador', on_delete='CASCADE')
    tag = CharField()
    nome_ad = CharField(null=True)
    numero_serie = CharField(null=True)
    data_fabricacao = DateField(null=True)

    class Meta:
        database = db


class Celular(Model):
    patrimonio = ForeignKeyField(Patrimonio, primary_key=True, backref='detalhes_celular', on_delete='CASCADE')
    modelo = CharField()
    numero_serie = CharField(null=True)
    email_vinculado = CharField(null=True)
    senha_google = CharField(null=True)
    senha_icloud = CharField(null=True)

    class Meta:
        database = db

    @staticmethod
    def _get_key():
        return current_app.config['SECRET_KEY']

    def senha_google_plain(self):
        return decrypt(self.senha_google, self._get_key())

    def set_senha_google(self, value):
        self.senha_google = encrypt(value, self._get_key()) if value else None

    def senha_icloud_plain(self):
        return decrypt(self.senha_icloud, self._get_key())

    def set_senha_icloud(self, value):
        self.senha_icloud = encrypt(value, self._get_key()) if value else None


class NumeroTelefone(Model):
    id = AutoField()
    numero = CharField()
    operadora = CharField()
    celular = ForeignKeyField(Celular, backref='numeros', null=True, on_delete='SET NULL')
    observacoes = TextField(null=True)

    class Meta:
        database = db


class TelefoneIP(Model):
    patrimonio = ForeignKeyField(Patrimonio, primary_key=True, backref='detalhes_telefone', on_delete='CASCADE')
    tag = CharField(null=True)
    ramal = CharField()
    modelo = CharField(null=True)

    class Meta:
        database = db


class Impressora(Model):
    patrimonio = ForeignKeyField(Patrimonio, primary_key=True, backref='detalhes_impressora', on_delete='CASCADE')
    marca = CharField()
    modelo = CharField()
    numero_serie = CharField(null=True)

    class Meta:
        database = db


class ItemDiverso(Model):
    patrimonio = ForeignKeyField(Patrimonio, primary_key=True, backref='detalhes_diverso', on_delete='CASCADE')
    nome = CharField()
    tipo_item = CharField()
    numero_serie = CharField(null=True)

    class Meta:
        database = db


class Auditoria(Model):
    id = AutoField()
    patrimonio = ForeignKeyField(Patrimonio, backref='auditorias', on_delete='CASCADE')
    data_auditoria = DateTimeField(default=utcnow)
    setor_no_momento = ForeignKeyField(Setor, null=True, on_delete='SET NULL')
    tecnico = ForeignKeyField(User, null=True, on_delete='SET NULL')
    uploaded_by = ForeignKeyField(User, null=True, on_delete='SET NULL')
    status_geral_ok = BooleanField(default=True)
    observacoes = TextField(null=True)
    tipo_dispositivo = CharField(max_length=20)

    class Meta:
        database = db
        indexes = (
            (('patrimonio', 'data_auditoria'), False),
        )


class AuditoriaCelular(Model):
    auditoria = ForeignKeyField(Auditoria, backref='detalhes_celular', unique=True, on_delete='CASCADE')
    apps_ok = BooleanField()
    fotos_ok = BooleanField()
    informacoes_ok = BooleanField()
    whatsapp_ok = BooleanField()
    avarias_ok = BooleanField()

    class Meta:
        database = db


class AuditoriaComputador(Model):
    auditoria = ForeignKeyField(Auditoria, backref='detalhes_computador', unique=True, on_delete='CASCADE')

    hardware_integro = BooleanField()
    bateria_ok = BooleanField()
    perifericos_ok = BooleanField()
    limpeza_fisica_ok = BooleanField()

    antivirus_ok = BooleanField()
    criptografia_ok = BooleanField()
    updates_ok = BooleanField()
    softwares_ok = BooleanField()

    dominio_ok = BooleanField()
    vpn_ok = BooleanField()
    limpeza_disco_ok = BooleanField()

    alocacao_ok = BooleanField()
    etiqueta_legivel = BooleanField()

    class Meta:
        database = db


class AuditoriaTelefone(Model):
    auditoria = ForeignKeyField(Auditoria, backref='detalhes_telefone', unique=True, on_delete='CASCADE')
    chamada_ok = BooleanField()
    fone_ok = BooleanField()
    cabo_rede_ok = BooleanField()
    poe_ok = BooleanField()
    etiqueta_legivel = BooleanField()

    class Meta:
        database = db


class AuditoriaImpressora(Model):
    auditoria = ForeignKeyField(Auditoria, backref='detalhes_impressora', unique=True, on_delete='CASCADE')
    liga_ok = BooleanField()
    qualidade_impressao_ok = BooleanField()
    scanner_ok = BooleanField()
    nivel_suprimentos_ok = BooleanField()
    cabos_ok = BooleanField()

    class Meta:
        database = db


class AuditoriaItemDiverso(Model):
    auditoria = ForeignKeyField(Auditoria, backref='detalhes_diverso', unique=True, on_delete='CASCADE')
    estado_fisico_ok = BooleanField()
    funcionamento_ok = BooleanField()
    acessorios_ok = BooleanField()
    etiqueta_legivel = BooleanField()

    class Meta:
        database = db


class AuditoriaAnexo(Model):
    id = AutoField()
    auditoria = ForeignKeyField(Auditoria, backref='anexos', on_delete='CASCADE')
    filename = CharField()
    stored_filename = CharField()
    mimetype = CharField()
    filesize = IntegerField()
    uploaded_by = ForeignKeyField(User, null=True, on_delete='SET NULL')
    criado_em = DateTimeField(default=utcnow)

    class Meta:
        database = db


class ItemAnexo(Model):
    id = AutoField()
    patrimonio = ForeignKeyField(Patrimonio, backref='fotos', on_delete='CASCADE')
    filename = CharField()
    stored_filename = CharField()
    mimetype = CharField()
    filesize = IntegerField()
    uploaded_by = ForeignKeyField(User, null=True, on_delete='SET NULL')
    criado_em = DateTimeField(default=utcnow)

    class Meta:
        database = db


def criar_auditoria(patrimonio, dados_comuns, dados_especificos, tecnico=None, uploaded_by=None):
    with db.atomic():
        auditoria = Auditoria.create(
            patrimonio=patrimonio,
            data_auditoria=utcnow(),
            setor_no_momento=patrimonio.setor,
            tecnico=tecnico,
            uploaded_by=uploaded_by,
            status_geral_ok=dados_comuns.get('status_geral_ok', True),
            observacoes=dados_comuns.get('observacoes'),
            tipo_dispositivo=patrimonio.tipo
        )
        tipo = patrimonio.tipo
        if tipo == TipoEquipamento.CELULAR.value:
            AuditoriaCelular.create(auditoria=auditoria, **dados_especificos)
        elif tipo == TipoEquipamento.COMPUTADOR.value:
            AuditoriaComputador.create(auditoria=auditoria, **dados_especificos)
        elif tipo == TipoEquipamento.TELEFONE.value:
            AuditoriaTelefone.create(auditoria=auditoria, **dados_especificos)
        elif tipo == TipoEquipamento.IMPRESSORA.value:
            AuditoriaImpressora.create(auditoria=auditoria, **dados_especificos)
        elif tipo == TipoEquipamento.ITEM_DIVERSO.value:
            AuditoriaItemDiverso.create(auditoria=auditoria, **dados_especificos)
        return auditoria
