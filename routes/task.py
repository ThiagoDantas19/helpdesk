import os
import csv
from io import StringIO
from math import ceil
from flask import Blueprint, render_template, request, redirect, abort, send_from_directory, Response
from flask_login import login_required, current_user
from routes.auth import admin_required, tecnico_required, pode_ver_chamado
from database.models.chamados import Chamado, ChamadoEquipamento, ChamadoAnexo
from database.models.usuarios import User, Setor
from database.models.equipamentos import Patrimonio, Computador, Celular, TelefoneIP, Impressora, ItemDiverso
from utils.constants import TipoEquipamento, TipoAcesso
from utils.compartilhado import salvar_anexos_chamado, UPLOAD_DIR
from utils.time import utcnow, hora_local, intervalo_dia_local_para_utc
from peewee import prefetch
from datetime import datetime

task_route = Blueprint('task', __name__)


def _parse_filtro_data(data_str):
    if not data_str:
        return ''
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        return data_str


@task_route.route('/', methods=['GET'])
@login_required
def lista_chamados():
    titulo = request.args.get('titulo', '')
    status = request.args.get('status', '')
    categoria = request.args.get('categoria', '')
    prioridade = request.args.get('prioridade', '')
    data_inicio_raw = request.args.get('data_inicio', '')
    data_fim_raw = request.args.get('data_fim', '')
    data_inicio = _parse_filtro_data(data_inicio_raw)
    data_fim = _parse_filtro_data(data_fim_raw)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)

    query = Chamado.select()

    if current_user.tipo_acesso == 'usuario':
        query = query.where(Chamado.funcionario == current_user.id)

    if titulo:
        query = query.where(Chamado.titulo.contains(titulo))
    if status:
        query = query.where(Chamado.status == status)
    if categoria:
        query = query.where(Chamado.categoria == categoria)
    if prioridade:
        query = query.where(Chamado.prioridade == prioridade)
    if data_inicio:
        try:
            inicio_utc, _ = intervalo_dia_local_para_utc(data_inicio)
            query = query.where(Chamado.criado_em >= inicio_utc)
        except ValueError:
            pass
    if data_fim:
        try:
            _, fim_utc = intervalo_dia_local_para_utc(data_fim)
            query = query.where(Chamado.criado_em < fim_utc)
        except ValueError:
            pass

    total = query.count()
    per_page = min(max(per_page, 10), 100)
    pages = max(1, ceil(total / per_page))
    page = max(1, min(page, pages))
    chamados = query.order_by(Chamado.criado_em.desc()).paginate(page, per_page)

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    template = 'chamado/lista_chamados.html' if is_ajax else 'chamado/lista_chamados_full.html'
    return render_template(template,
                           chamados=chamados,
                           titulo=titulo, status=status, categoria=categoria, prioridade=prioridade,
                           data_inicio=data_inicio_raw, data_fim=data_fim_raw,
                           page=page, per_page=per_page, total=total, pages=pages)


@task_route.route('/', methods=['POST'])
@login_required
def abrir_chamados():
    if current_user.tipo_acesso == TipoAcesso.USUARIO.value:
        funcionario_id = current_user.id
    else:
        funcionario_id = request.form.get('funcionario_id') or current_user.id

    chamado = Chamado.create(
        titulo=request.form.get('titulo'),
        descricao=request.form.get('descricao'),
        prioridade=request.form.get('prioridade'),
        categoria=request.form.get('categoria'),
        status='aberto',
        funcionario=funcionario_id
    )

    salvar_anexos_chamado(chamado, request.files.getlist('anexos'))

    equipamentos_selecionados = request.form.getlist('equipamentos_ids')
    for item in equipamentos_selecionados:
        if item and "_" in item:
            tipo, eq_id = item.rsplit("_", 1)
            if eq_id.isdigit():
                ChamadoEquipamento.create(
                    chamado=chamado,
                    tipo_equipamento=tipo,
                    equipamento_id=int(eq_id)
                )

    return redirect('/')


@task_route.route('/new', methods=['GET'])
@login_required
def form_chamado():
    computadores = Computador.select().join(Patrimonio).where(Patrimonio.ativo == True)
    celulares = Celular.select().join(Patrimonio).where(Patrimonio.ativo == True)
    telefones_ip = TelefoneIP.select().join(Patrimonio).where(Patrimonio.ativo == True)
    impressoras = Impressora.select().join(Patrimonio).where(Patrimonio.ativo == True)
    itens_diversos = ItemDiverso.select().join(Patrimonio).where(Patrimonio.ativo == True)

    ctx = dict(
        computadores=computadores,
        celulares=celulares,
        telefones_ip=telefones_ip,
        impressoras=impressoras,
        itens_diversos=itens_diversos,
    )

    if current_user.tipo_acesso in ('admin', 'tecnico'):
        funcionarios = User.select().where(User.ativo == True)
        ctx['funcionarios'] = funcionarios

    return render_template('chamado/form_chamados.html', **ctx)


def _resolve_equipamentos(chamado):
    vinculos = ChamadoEquipamento.select().where(ChamadoEquipamento.chamado == chamado)
    equipamentos = []
    for v in vinculos:
        tipo = v.tipo_equipamento
        nome = f'{tipo} #{v.equipamento_id}'
        url = None
        try:
            if tipo == TipoEquipamento.COMPUTADOR.value:
                eq = Computador.get_by_id(v.equipamento_id)
                nome = f'{eq.nome_ad or eq.tag or "Computador"}'
                url = f'/inventario/computador/{v.equipamento_id}'
            elif tipo == TipoEquipamento.CELULAR.value:
                eq = Celular.get_by_id(v.equipamento_id)
                nome = eq.modelo
                url = f'/inventario/celular/{v.equipamento_id}'
            elif tipo == TipoEquipamento.TELEFONE.value:
                eq = TelefoneIP.get_by_id(v.equipamento_id)
                nome = f'Ramal {eq.ramal}'
                url = f'/inventario/telefone/{v.equipamento_id}'
            elif tipo == TipoEquipamento.IMPRESSORA.value:
                eq = Impressora.get_by_id(v.equipamento_id)
                nome = f'{eq.marca} {eq.modelo}'
                url = f'/inventario/impressora/{v.equipamento_id}'
            elif tipo == TipoEquipamento.ITEM_DIVERSO.value:
                eq = ItemDiverso.get_by_id(v.equipamento_id)
                nome = eq.nome
                url = f'/inventario/item/{v.equipamento_id}'
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Erro ao resolver equipamento %s #%s', tipo, v.equipamento_id)
        equipamentos.append({'tipo': tipo, 'nome': nome, 'url': url})
    return equipamentos


@task_route.route('/<int:os_id>', methods=['GET'])
@login_required
def detalhes_chamados(os_id):
    chamado = Chamado.get_by_id(os_id)
    if not pode_ver_chamado(chamado):
        abort(403)
    equipamentos = _resolve_equipamentos(chamado)
    anexos = ChamadoAnexo.select().where(ChamadoAnexo.chamado == chamado).order_by(ChamadoAnexo.criado_em.desc())
    return render_template('chamado/det_chamados.html', chamado=chamado, equipamentos=equipamentos, anexos=anexos)


@task_route.route('/<int:os_id>/assumir', methods=['POST'])
@login_required
@tecnico_required
def assumir_chamado(os_id):
    chamado = Chamado.get_by_id(os_id)
    chamado.operador = current_user.id
    chamado.status = 'em_andamento'
    chamado.atualizado_em = utcnow()
    chamado.save()
    return redirect(f'/task/{os_id}')


@task_route.route('/<int:os_id>/responder', methods=['POST'])
@login_required
@tecnico_required
def responder_chamado(os_id):
    chamado = Chamado.get_by_id(os_id)
    data = request.form
    chamado.resposta = data.get('resposta')
    chamado.nota_interna = data.get('nota_interna')
    chamado.status = data.get('status', chamado.status)
    chamado.operador = chamado.operador or current_user.id
    chamado.atualizado_em = utcnow()
    if chamado.status == 'fechado' and not chamado.fechado_em:
        chamado.fechado_em = utcnow()
    chamado.save()
    return redirect(f'/task/{os_id}')


@task_route.route('/<int:os_id>/edit', methods=['GET'])
@login_required
@admin_required
def form_edit_detalhes_chamados(os_id):
    chamado = Chamado.get_by_id(os_id)
    funcionarios = User.select().where(User.ativo == True)

    computadores = Computador.select().join(Patrimonio).where(Patrimonio.ativo == True)
    celulares = Celular.select().join(Patrimonio).where(Patrimonio.ativo == True)
    telefones_ip = TelefoneIP.select().join(Patrimonio).where(Patrimonio.ativo == True)
    impressoras = Impressora.select().join(Patrimonio).where(Patrimonio.ativo == True)
    itens_diversos = ItemDiverso.select().join(Patrimonio).where(Patrimonio.ativo == True)

    vinc_query = ChamadoEquipamento.select().where(ChamadoEquipamento.chamado == chamado)
    equipamentos_vinculados = {f"{v.tipo_equipamento}_{v.equipamento_id}" for v in vinc_query}

    anexos = ChamadoAnexo.select().where(ChamadoAnexo.chamado == chamado).order_by(ChamadoAnexo.criado_em.desc())

    return render_template(
        'chamado/form_edit_chamado.html',
        chamado=chamado, funcionarios=funcionarios,
        computadores=computadores, celulares=celulares, telefones_ip=telefones_ip,
        impressoras=impressoras, itens_diversos=itens_diversos,
        equipamentos_vinculados=equipamentos_vinculados, anexos=anexos
    )


@task_route.route('/<int:os_id>/update', methods=['POST'])
@login_required
@admin_required
def update_chamados(os_id):
    chamado = Chamado.get_by_id(os_id)

    mapping = {
        'titulo': 'titulo', 'descricao': 'descricao', 'prioridade': 'prioridade',
        'categoria': 'categoria', 'status': 'status', 'resposta': 'resposta', 'nota_interna': 'nota_interna',
    }
    for k, v in mapping.items():
        val = request.form.get(k)
        if val is not None:
            setattr(chamado, v, val)

    if request.form.get('funcionario_id'):
        chamado.funcionario = request.form.get('funcionario_id')

    chamado.atualizado_em = utcnow()

    if chamado.status == 'fechado' and not chamado.fechado_em:
        chamado.fechado_em = utcnow()

    chamado.save()
    salvar_anexos_chamado(chamado, request.files.getlist('anexos'))

    ids_recebidos = set()
    for item in request.form.getlist('equipamentos_ids'):
        if item and "_" in item:
            ids_recebidos.add(item)

    if ids_recebidos:
        existentes = set()
        for v in ChamadoEquipamento.select().where(ChamadoEquipamento.chamado == chamado):
            chave = f"{v.tipo_equipamento}_{v.equipamento_id}"
            existentes.add(chave)

        para_remover = existentes - ids_recebidos
        if para_remover:
            cond = None
            for chave in para_remover:
                tipo, eq_id = chave.rsplit("_", 1)
                clause = (ChamadoEquipamento.chamado == chamado) & (ChamadoEquipamento.tipo_equipamento == tipo) & (ChamadoEquipamento.equipamento_id == int(eq_id))
                cond = clause if cond is None else (cond | clause)
            if cond is not None:
                ChamadoEquipamento.delete().where(cond).execute()

        para_adicionar = ids_recebidos - existentes
        for chave in para_adicionar:
            tipo, eq_id = chave.rsplit("_", 1)
            ChamadoEquipamento.create(chamado=chamado, tipo_equipamento=tipo, equipamento_id=int(eq_id))
    else:
        ChamadoEquipamento.delete().where(ChamadoEquipamento.chamado == chamado).execute()

    return redirect('/')


@task_route.route('/<int:os_id>/anexar', methods=['POST'])
@login_required
def anexar_arquivo(os_id):
    chamado = Chamado.get_by_id(os_id)
    if not pode_ver_chamado(chamado):
        abort(403)
    salvar_anexos_chamado(chamado, request.files.getlist('anexos'))
    return redirect(f'/task/{os_id}')


@task_route.route('/uploads/<filename>')
@login_required
def servir_anexo(filename):
    if '/' in filename or '..' in filename:
        abort(404)
    anexo = ChamadoAnexo.get_or_none(ChamadoAnexo.stored_filename == filename)
    if not anexo or not pode_ver_chamado(anexo.chamado):
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename)


@task_route.route('/<int:os_id>/anexo/<int:anexo_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_anexo(os_id, anexo_id):
    anexo = ChamadoAnexo.get_or_none(
        (ChamadoAnexo.id == anexo_id) & (ChamadoAnexo.chamado == os_id)
    )
    if not anexo:
        abort(404)
    caminho = os.path.join(UPLOAD_DIR, anexo.stored_filename)
    if os.path.exists(caminho):
        os.remove(caminho)
    anexo.delete_instance()
    return {'deleted': 'ok'}


@task_route.route('/<int:os_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_chamados(os_id):
    chamado = Chamado.get_by_id(os_id)
    for anexo in ChamadoAnexo.select().where(ChamadoAnexo.chamado == chamado):
        caminho = os.path.join(UPLOAD_DIR, anexo.stored_filename)
        if os.path.exists(caminho):
            os.remove(caminho)
        anexo.delete_instance()
    chamado.delete_instance()
    return {'deleted': 'ok'}


@task_route.route('/exportar', methods=['GET'])
@login_required
@tecnico_required
def exportar_chamados_csv():
    query = Chamado.select().order_by(Chamado.criado_em.desc())
    chamados = prefetch(query, User, Setor)

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Titulo', 'Descricao', 'Status', 'Prioridade', 'Categoria',
                 'Solicitante', 'Setor', 'Operador', 'Criado Em', 'Atualizado Em', 'Fechado Em', 'Resposta'])
    for c in chamados:
        cw.writerow([
            c.id, c.titulo, c.descricao, c.status, c.prioridade, c.categoria,
            c.funcionario.nome_completo,
            c.funcionario.setor.nome if c.funcionario.setor else '',
            c.operador.nome_completo if c.operador else '',
            hora_local(c.criado_em).strftime('%d/%m/%Y %H:%M') if c.criado_em else '',
            hora_local(c.atualizado_em).strftime('%d/%m/%Y %H:%M') if c.atualizado_em else '',
            hora_local(c.fechado_em).strftime('%d/%m/%Y %H:%M') if c.fechado_em else '',
            c.resposta or ''
        ])
    response = Response(si.getvalue(), mimetype='text/csv')
    response.headers['Content-disposition'] = f'attachment; filename=chamados_{hora_local(utcnow()).strftime("%Y%m%d")}.csv'
    return response
