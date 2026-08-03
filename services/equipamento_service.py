import os
import re
import logging
from math import ceil
from types import SimpleNamespace
from flask import render_template, redirect, flash, make_response
from flask_login import current_user
from peewee import prefetch
from database.database import db
from database.models.equipamentos import (
    Patrimonio, Auditoria, AuditoriaAnexo, ItemAnexo, criar_auditoria
)
from database.models.usuarios import User, Setor
from database.models.chamados import Chamado, ChamadoEquipamento
from database.models.log import registrar_log
from utils.compartilhado import validar_arquivo, salvar_midia, UPLOAD_DIR, export_auditoria_csv
from utils.cache import get as cache_get, set as cache_set
from utils.constants import TipoEquipamento

logger = logging.getLogger(__name__)


class EquipamentoService:
    _registry = {}

    @classmethod
    def get_for_tipo(cls, tipo):
        return cls._registry.get(tipo)

    def __init__(self, model_cls, tipo, template_prefix, var_name,
                 var_name_plural=None,
                 auditoria_cls=None, auditoria_itens=None,
                 nome_identificador_fn=None, csv_header=None, csv_row_fn=None,
                 allow_inativos=False):
        self.model_cls = model_cls
        self.tipo = tipo
        self.template_prefix = template_prefix
        self.var_name = var_name
        self.var_name_plural = var_name_plural or (var_name + 's')
        self._registry[tipo] = self
        self.auditoria_cls = auditoria_cls
        self.auditoria_itens = auditoria_itens or []
        self.nome_identificador_fn = nome_identificador_fn or (lambda d: d.get('nome_identificador', ''))
        self.csv_header = csv_header
        self.csv_row_fn = csv_row_fn
        self.allow_inativos = allow_inativos

    def _query_lista(self):
        q = self.model_cls.select(self.model_cls, Patrimonio).join(Patrimonio)
        if not self.allow_inativos:
            q = q.where(Patrimonio.ativo == True)
        return q.order_by(Patrimonio.codigo_etiqueta)

    def lista(self, page=1, per_page=25):
        query = self._query_lista()
        total = query.count()
        pages = ceil(total / per_page)
        itens = query.paginate(page, per_page)
        return render_template(
            f'inventario/{self.template_prefix}/lista.html',
            **{self.var_name_plural: list(itens), 'page': page, 'pages': pages, 'total': total}
        )

    def get_form_context(self):
        setores = cache_get('setores_ordenados')
        if setores is None:
            setores = [{'id': s.id, 'nome': s.nome} for s in Setor.select().order_by(Setor.nome)]
            cache_set('setores_ordenados', setores)
        setores = [SimpleNamespace(**d) for d in setores]
        return {
            'usuarios': User.select().where(User.ativo == True).order_by(User.nome_completo),
            'setores': setores
        }

    def _validar_setor_responsavel(self, data):
        setor_id = data.get('setor_id')
        responsavel_id = data.get('responsavel_id')
        if setor_id and responsavel_id:
            user = User.get_or_none(User.id == int(responsavel_id))
            if user and user.setor_id and str(user.setor_id) != str(setor_id):
                flash(f'{user.nome_completo} não pertence ao setor selecionado.', 'danger')
                return False
        return True

    def _validar_codigo_etiqueta(self, data):
        codigo = data.get('codigo_etiqueta') or data.get('patrimonio') or ''
        codigo = codigo.strip()
        if not codigo:
            return True
        if len(codigo) > 4:
            flash('O código de patrimônio deve ter no máximo 4 dígitos.', 'danger')
            return False
        if not re.match(r'^\d{1,4}$', codigo):
            flash('O código de patrimônio deve conter apenas números (máx. 4 dígitos).', 'danger')
            return False
        return True

    def criar(self, data, extra_fields_fn=None, after_create_fn=None):
        if not self._validar_setor_responsavel(data) or not self._validar_codigo_etiqueta(data):
            return redirect(f'/inventario/{self.template_prefix}/')
        try:
            with db.atomic():
                novo_patrimonio = Patrimonio.create(
                    codigo_etiqueta=data.get('codigo_etiqueta') or data.get('patrimonio') or None,
                    nome_identificador=self.nome_identificador_fn(data),
                    tipo=self.tipo.value if isinstance(self.tipo, TipoEquipamento) else self.tipo,
                    setor=data.get('setor_id') or None,
                    responsavel=data.get('responsavel_id') or None,
                    observacoes=data.get('observacoes'),
                    ativo=True
                )
                extra = extra_fields_fn(data) if extra_fields_fn else {}
                obj = self.model_cls.create(patrimonio=novo_patrimonio, **extra)
                if after_create_fn:
                    after_create_fn(obj, data)
            registrar_log(current_user, 'criar', entidade=self.tipo.value if isinstance(self.tipo, TipoEquipamento) else self.tipo, entidade_id=novo_patrimonio.id, descricao=f'{self.template_prefix} criado.')
            flash(f'{self.var_name.capitalize()} criado com sucesso.', 'success')
            return redirect(f'/inventario/{self.template_prefix}/')
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(f'/inventario/{self.template_prefix}/')
        except Exception:
            logger.exception(f'Erro ao criar {self.template_prefix}')
            flash(f'Erro ao criar {self.template_prefix}. Verifique os dados e tente novamente.', 'danger')
            return redirect(f'/inventario/{self.template_prefix}/')

    def _get_obj(self, patr_id):
        return self.model_cls.select(self.model_cls, Patrimonio).join(Patrimonio).where(Patrimonio.id == patr_id).get()

    def detalhes(self, patr_id, extra_context_fn=None, chamado_filtro_extra=None):
        obj = self._get_obj(patr_id)
        cond = (ChamadoEquipamento.equipamento_id == patr_id)
        if chamado_filtro_extra:
            cond = cond & chamado_filtro_extra
        chamados = (Chamado.select()
                    .join(ChamadoEquipamento)
                    .where(cond)
                    .order_by(Chamado.criado_em.desc()))
        ultima_auditoria = (Auditoria
            .select()
            .where(Auditoria.patrimonio == patr_id)
            .order_by(Auditoria.data_auditoria.desc())
            .first())
        fotos = (ItemAnexo
            .select()
            .where(ItemAnexo.patrimonio == patr_id)
            .order_by(ItemAnexo.criado_em.desc()))
        ctx = {
            self.var_name: obj,
            'chamados': list(chamados),
            'ultima_auditoria': ultima_auditoria,
            'fotos': list(fotos),
        }
        if extra_context_fn:
            ctx.update(extra_context_fn(obj))
        return render_template(f'inventario/{self.template_prefix}/det.html', **ctx)

    def atualizar(self, patr_id, data, update_fn=None):
        if not self._validar_setor_responsavel(data) or not self._validar_codigo_etiqueta(data):
            return redirect(f'/inventario/{self.template_prefix}/{patr_id}')
        try:
            with db.atomic():
                obj = self.model_cls.get_by_id(patr_id)
                p = obj.patrimonio
                p.codigo_etiqueta = data.get('codigo_etiqueta') or data.get('patrimonio') or None
                p.nome_identificador = self.nome_identificador_fn(data) or p.nome_identificador
                p.setor = data.get('setor_id') or None
                p.responsavel = data.get('responsavel_id') or None
                p.observacoes = data.get('observacoes')
                p.ativo = (data.get('ativo') == '1')
                p.save()
                if update_fn:
                    update_fn(obj, data)
                else:
                    obj.save()
            registrar_log(current_user, 'atualizar', entidade=self.tipo.value if isinstance(self.tipo, TipoEquipamento) else self.tipo, entidade_id=patr_id, descricao=f'{self.template_prefix} atualizado.')
            flash(f'{self.var_name.capitalize()} atualizado com sucesso.', 'success')
            return redirect(f'/inventario/{self.template_prefix}/')
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(f'/inventario/{self.template_prefix}/{patr_id}')
        except Exception:
            logger.exception(f'Erro ao atualizar {self.template_prefix}')
            flash(f'Erro ao atualizar {self.template_prefix}.', 'danger')
            return redirect(f'/inventario/{self.template_prefix}/{patr_id}')

    def form_edit(self, patr_id):
        obj = self._get_obj(patr_id)
        context = self.get_form_context()
        context[self.var_name] = obj
        return render_template(f'inventario/{self.template_prefix}/form_edit.html', **context)

    def form_auditoria(self, patr_id):
        obj = self._get_obj(patr_id)
        resp = make_response(render_template(f'inventario/{self.template_prefix}/form_auditoria.html', **{self.var_name: obj}))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp

    def post_auditoria(self, patr_id, form_data, files):
        patrimonio = Patrimonio.get_by_id(patr_id)
        dados_especificos = {k: k in form_data for k in self.auditoria_itens}
        dados_comuns = {
            'status_geral_ok': all(dados_especificos.values()),
            'observacoes': form_data.get('observacoes')
        }
        auditoria = criar_auditoria(
            patrimonio, dados_comuns, dados_especificos,
            tecnico=current_user.id, uploaded_by=current_user.id
        )
        for f in files.getlist('fotos'):
            if validar_arquivo(f):
                stored = salvar_midia(f)
                AuditoriaAnexo.create(
                    auditoria=auditoria,
                    filename=f.filename,
                    stored_filename=stored,
                    mimetype=f.content_type or 'application/octet-stream',
                    filesize=os.path.getsize(os.path.join(UPLOAD_DIR, stored)),
                    uploaded_by=current_user.id
                )
        return redirect(f'/inventario/{self.template_prefix}/{patr_id}')

    def form_edit_auditoria(self, audit_id):
        auditoria = Auditoria.get_by_id(audit_id)
        patr_id = auditoria.patrimonio_id
        obj = self._get_obj(patr_id)
        detalhes_cls = self.auditoria_cls
        detalhes = detalhes_cls.get_or_none(detalhes_cls.auditoria == audit_id)
        detalhes_dict = {item: getattr(detalhes, item, False) for item in self.auditoria_itens} if detalhes else {}
        anexos = (AuditoriaAnexo.select().where(AuditoriaAnexo.auditoria == audit_id)
                   .order_by(AuditoriaAnexo.criado_em.desc()))
        return render_template(
            'inventario/form_auditoria_edit.html',
            **{self.var_name: obj, 'auditoria': auditoria, 'detalhes_dict': detalhes_dict,
               'auditoria_itens': self.auditoria_itens, 'template_prefix': self.template_prefix,
               'anexos': list(anexos)}
        )

    def update_auditoria(self, audit_id, form_data, files):
        auditoria = Auditoria.get_by_id(audit_id)
        detalhes_cls = self.auditoria_cls
        detalhes = detalhes_cls.get_or_none(detalhes_cls.auditoria == audit_id)
        if detalhes:
            for item in self.auditoria_itens:
                setattr(detalhes, item, item in form_data)
            detalhes.save()
        status_ok = all(item in form_data for item in self.auditoria_itens)
        auditoria.status_geral_ok = status_ok
        auditoria.observacoes = form_data.get('observacoes')
        auditoria.save()
        for f in files.getlist('fotos'):
            if validar_arquivo(f):
                stored = salvar_midia(f)
                AuditoriaAnexo.create(
                    auditoria=auditoria,
                    filename=f.filename,
                    stored_filename=stored,
                    mimetype=f.content_type or 'application/octet-stream',
                    filesize=os.path.getsize(os.path.join(UPLOAD_DIR, stored)),
                    uploaded_by=current_user.id
                )
        registrar_log(current_user, 'atualizar', entidade='auditoria', entidade_id=audit_id,
                      descricao=f'Auditoria #{audit_id} atualizada.')
        flash('Auditoria atualizada com sucesso.', 'success')
        return redirect(f'/inventario/{self.template_prefix}/{auditoria.patrimonio_id}/auditorias')

    def historico_auditorias(self, patr_id):
        obj = self._get_obj(patr_id)
        auditorias = Auditoria.select().where(Auditoria.patrimonio == patr_id).order_by(Auditoria.data_auditoria.desc())
        return render_template(
            f'inventario/{self.template_prefix}/historico.html',
            **{self.var_name: obj, 'auditorias': auditorias, 'AuditoriaAnexo': AuditoriaAnexo}
        )

    def deletar(self, patr_id):
        try:
            with db.atomic():
                p = Patrimonio.get_by_id(patr_id)
                ChamadoEquipamento.delete().where(
                    ChamadoEquipamento.equipamento_id == patr_id
                ).execute()

                arquivos = set()
                arquivos.update(a.stored_filename for a in (
                    AuditoriaAnexo
                    .select(AuditoriaAnexo.stored_filename)
                    .join(Auditoria)
                    .where(Auditoria.patrimonio == patr_id)))
                arquivos.update(f.stored_filename for f in (
                    ItemAnexo
                    .select(ItemAnexo.stored_filename)
                    .where(ItemAnexo.patrimonio == patr_id)))

                ids_auditorias = [
                    a.id for a in Auditoria
                    .select(Auditoria.id)
                    .where(Auditoria.patrimonio == patr_id)]
                if ids_auditorias:
                    self.auditoria_cls.delete().where(
                        self.auditoria_cls.auditoria.in_(ids_auditorias)
                    ).execute()

                p.delete_instance()

            for nome in arquivos:
                caminho = os.path.join(UPLOAD_DIR, nome)
                if os.path.exists(caminho):
                    os.remove(caminho)
            registrar_log(current_user, 'deletar',
                          entidade=self.tipo.value if isinstance(self.tipo, TipoEquipamento) else self.tipo,
                          entidade_id=patr_id,
                          descricao=f'{self.template_prefix} deletado.')
            return True
        except Exception:
            logger.exception(f'Erro ao deletar {self.template_prefix} #{patr_id}')
            return False

    def export_auditorias(self, patr_id):
        if self.csv_header and self.csv_row_fn:
            fk = self.auditoria_cls._meta.fields['auditoria']
            auditorias = prefetch(
                Auditoria.select()
                .where(Auditoria.patrimonio == patr_id)
                .order_by(Auditoria.data_auditoria.desc()),
                self.auditoria_cls
            )
            linhas = [(a, getattr(a, fk.backref)) for a in auditorias]
            return export_auditoria_csv(patr_id, self.csv_header, self.csv_row_fn, auditorias_query=linhas)
        return redirect(f'/inventario/{self.template_prefix}/{patr_id}')
