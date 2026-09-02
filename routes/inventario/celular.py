import os
import csv
from io import StringIO
from flask import Response, render_template, request, redirect, jsonify
from flask_login import login_required, current_user
from routes.auth import admin_required, tecnico_required
from utils.constants import TipoEquipamento
from utils.time import hora_local, fuso_padrao, utcnow, inicio_mes_utc, fim_mes_utc
from database.models.equipamentos import (
    Celular, Patrimonio, NumeroTelefone, Auditoria, AuditoriaCelular
)
from database.models.usuarios import Setor
from routes.inventario import inventario_route
from services.equipamento_service import EquipamentoService
from peewee import prefetch
from datetime import timezone


service = EquipamentoService(
    model_cls=Celular,
    tipo=TipoEquipamento.CELULAR,
    template_prefix='celular',
    var_name='celular',
    auditoria_cls=AuditoriaCelular,
    auditoria_itens=['apps_ok', 'fotos_ok', 'informacoes_ok', 'whatsapp_ok', 'avarias_ok'],
    nome_identificador_fn=lambda d: d.get('modelo'),
    csv_header=['Data', 'Setor', 'Apps', 'Fotos', 'Dados', 'WhatsApp', 'Avarias', 'Obs'],
    csv_row_fn=lambda a, d: _csv_row(a, d),
)


def _csv_row(a, d):
    return [
        hora_local(a.data_auditoria).strftime('%d/%m/%Y %H:%M'),
        a.setor_no_momento.nome if a.setor_no_momento else 'Sem setor',
        'OK' if d and d.apps_ok else 'ERRO',
        'OK' if d and d.fotos_ok else 'ERRO',
        'OK' if d and d.informacoes_ok else 'ERRO',
        'OK' if d and d.whatsapp_ok else 'ERRO',
        'OK' if d and d.avarias_ok else 'AVARIADO',
        a.observacoes or ''
    ]


def _extra_create(data):
    return {
        'modelo': data.get('modelo'),
        'numero_serie': data.get('numero_serie'),
        'email_vinculado': data.get('email_vinculado'),
    }


def _after_create(obj, data):
    obj.set_senha_google(data.get('senha_google'))
    obj.set_senha_icloud(data.get('senha_icloud'))
    obj.save()


def _extra_update(obj, data):
    obj.modelo = data.get('modelo')
    obj.numero_serie = data.get('numero_serie')
    obj.email_vinculado = data.get('email_vinculado')
    obj.set_senha_google(data.get('senha_google'))
    obj.set_senha_icloud(data.get('senha_icloud'))
    obj.save()


@inventario_route.route('/celular/', methods=['GET'])
@login_required
@tecnico_required
def lista_celulares():
    page = request.args.get('page', 1, type=int)
    POR_PAGINA = 25
    celulares_q = (Celular
                   .select(Celular, Patrimonio)
                   .join(Patrimonio)
                   .where(Patrimonio.ativo == True)
                   .order_by(Patrimonio.codigo_etiqueta))
    total = celulares_q.count()
    from math import ceil
    pages = ceil(total / POR_PAGINA)
    celulares_q_page = celulares_q.paginate(page, POR_PAGINA)
    numeros_q = NumeroTelefone.select()
    celulares = prefetch(celulares_q_page, numeros_q)
    auditados_mes = {a.patrimonio_id for a in Auditoria
                     .select(Auditoria.patrimonio_id)
                     .where(Auditoria.data_auditoria >= inicio_mes_utc(),
                            Auditoria.data_auditoria < fim_mes_utc())}
    return render_template('inventario/celular/lista.html', celulares=list(celulares), page=page, pages=pages, total=total, auditados_mes=auditados_mes)


@inventario_route.route('/celular/new', methods=['GET'])
@login_required
@admin_required
def form_celular():
    return render_template('inventario/celular/form.html', **service.get_form_context())


@inventario_route.route('/celular/', methods=['POST'])
@login_required
@admin_required
def criar_celular():
    return service.criar(request.form, extra_fields_fn=_extra_create, after_create_fn=_after_create)


@inventario_route.route('/celular/<int:patr_id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes_celular(patr_id):
    def extra(celular):
        linhas = list(NumeroTelefone.select().where(NumeroTelefone.celular == celular))
        auditorias = list(Auditoria.select().where(Auditoria.patrimonio == patr_id).order_by(Auditoria.data_auditoria.desc()))
        return {'linhas': linhas, 'auditorias': auditorias}
    return service.detalhes(patr_id, extra_context_fn=extra)


@inventario_route.route('/celular/<int:patr_id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_celular(patr_id):
    return service.form_edit(patr_id)


@inventario_route.route('/celular/<int:patr_id>/update', methods=['POST'])
@login_required
@admin_required
def update_celular(patr_id):
    return service.atualizar(patr_id, request.form, update_fn=_extra_update)


@inventario_route.route('/celular/<int:patr_id>/auditar', methods=['GET'])
@login_required
@tecnico_required
def form_auditoria_celular(patr_id):
    return service.form_auditoria(patr_id)


@inventario_route.route('/celular/<int:patr_id>/auditar', methods=['POST'])
@login_required
@admin_required
def post_auditoria_celular(patr_id):
    return service.post_auditoria(patr_id, request.form, request.files)


@inventario_route.route('/celular/<int:patr_id>/auditorias', methods=['GET'])
@login_required
@tecnico_required
def historico_auditorias_celular(patr_id):
    return service.historico_auditorias(patr_id)


@inventario_route.route('/celular/<int:patr_id>/auditorias/export', methods=['GET'])
@login_required
@tecnico_required
def export_auditorias_celular(patr_id):
    return service.export_auditorias(patr_id)


@inventario_route.route('/celular/export/mensal', methods=['GET'])
@login_required
@tecnico_required
def export_mensal_celulares():
    agora_local = hora_local(utcnow())
    inicio_mes = agora_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if agora_local.month == 12:
        fim_mes = agora_local.replace(year=agora_local.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        fim_mes = agora_local.replace(month=agora_local.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_mes = inicio_mes.replace(tzinfo=fuso_padrao()).astimezone(timezone.utc)
    fim_mes = fim_mes.replace(tzinfo=fuso_padrao()).astimezone(timezone.utc)

    auditorias = list((Auditoria
                       .select(Auditoria, Patrimonio, Celular)
                       .join(Patrimonio)
                       .join(Celular)
                       .where(Auditoria.data_auditoria >= inicio_mes,
                              Auditoria.data_auditoria < fim_mes)
                       .order_by(Auditoria.data_auditoria.desc())))

    ids_auditorias = [a.id for a in auditorias]
    ids_patrimonios = {a.patrimonio_id for a in auditorias}
    celulares = {c.patrimonio_id: c for c in Celular
                 .select()
                 .where(Celular.patrimonio.in_(ids_patrimonios))}
    detalhes = {d.auditoria_id: d for d in AuditoriaCelular
                .select()
                .where(AuditoriaCelular.auditoria.in_(ids_auditorias))}
    setores = {s.id: s for s in Setor
               .select()
               .where(Setor.id.in_([a.setor_no_momento_id for a in auditorias]))}

    si = StringIO()
    si.write('\ufeff')
    cw = csv.writer(si, delimiter=';')
    cw.writerow(['Patrimonio', 'Modelo', 'Data Auditoria', 'Setor', 'Apps', 'Fotos', 'WhatsApp', 'Sem Avarias', 'Observacoes'])
    for a in auditorias:
        cel = celulares.get(a.patrimonio_id)
        d = detalhes.get(a.id)
        setor = setores.get(a.setor_no_momento_id)
        modelo = cel.modelo if cel else "N/A"
        cw.writerow([
            a.patrimonio.codigo_etiqueta,
            modelo,
            hora_local(a.data_auditoria).strftime('%d/%m/%Y %H:%M'),
            setor.nome if setor else 'Sem setor',
            'OK' if d and d.apps_ok else 'Falha',
            'OK' if d and d.fotos_ok else 'Falha',
            'OK' if d and d.whatsapp_ok else 'Falha',
            'Sim' if d and d.avarias_ok else 'Não (Avaria Detectada)',
            a.observacoes or ''
        ])
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=relatorio_mensal_{agora_local.strftime('%m_%Y')}.csv"}
    )


@inventario_route.route('/celular/<int:patr_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_celular(patr_id):
    if service.deletar(patr_id):
        return jsonify({'deleted': 'ok'})
    return jsonify({'erro': 'Não encontrado ou falha ao excluir'}), 404
