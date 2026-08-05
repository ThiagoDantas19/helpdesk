import os
from flask import Blueprint, render_template, request, redirect, send_from_directory, abort, jsonify
from flask_login import login_required, current_user
from routes.auth import admin_required, tecnico_required
from database.models.equipamentos import (
    Patrimonio, Auditoria, AuditoriaAnexo, ItemAnexo
)
from utils.constants import TipoEquipamento
from utils.compartilhado import validar_arquivo, salvar_midia, UPLOAD_DIR

inventario_route = Blueprint('inventario', __name__)


@inventario_route.route('/patrimonio/verificar', methods=['GET'])
@login_required
@admin_required
def verificar_patrimonio():
    codigo = request.args.get('codigo', '').strip()
    excluir = request.args.get('excluir', type=int)
    if not codigo:
        return jsonify({'disponivel': True, 'identificacao': ''})
    query = Patrimonio.select().where(Patrimonio.codigo_etiqueta == codigo)
    if excluir:
        query = query.where(Patrimonio.id != excluir)
    existente = query.first()
    if not existente:
        return jsonify({'disponivel': True, 'identificacao': ''})
    rotulo = TipoEquipamento(existente.tipo).url_name() if existente.tipo in TipoEquipamento.list() else existente.tipo
    identificacao = f'{rotulo}: {existente.nome_identificador}'
    return jsonify({'disponivel': False, 'identificacao': identificacao})


@inventario_route.route('/')
@login_required
@tecnico_required
def hub():
    return render_template('inventario/hub.html')


@inventario_route.route('/uploads/<filename>')
@login_required
@tecnico_required
def servir_midia(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@inventario_route.route('/auditoria/<int:audit_id>/anexar', methods=['POST'])
@login_required
@admin_required
def anexar_midia_auditoria(audit_id):
    auditoria = Auditoria.get_by_id(audit_id)
    for f in request.files.getlist('midia'):
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
    tipo_url = auditoria.patrimonio.tipo.replace('_', '')
    if tipo_url == 'itemdiverso':
        tipo_url = 'item'
    return redirect(f'/inventario/{tipo_url}/{auditoria.patrimonio_id}/auditorias')


@inventario_route.route('/auditoria/anexo/<int:anexo_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_midia_auditoria(anexo_id):
    anexo = AuditoriaAnexo.get_by_id(anexo_id)
    caminho = os.path.join(UPLOAD_DIR, anexo.stored_filename)
    if os.path.exists(caminho):
        os.remove(caminho)
    anexo.delete_instance()
    return {'deleted': 'ok'}


@inventario_route.route('/item/<int:patr_id>/foto', methods=['POST'])
@login_required
@admin_required
def anexar_foto_item(patr_id):
    patrimonio = Patrimonio.get_by_id(patr_id)
    for f in request.files.getlist('fotos'):
        if validar_arquivo(f):
            stored = salvar_midia(f)
            ItemAnexo.create(
                patrimonio=patrimonio,
                filename=f.filename,
                stored_filename=stored,
                mimetype=f.content_type or 'application/octet-stream',
                filesize=os.path.getsize(os.path.join(UPLOAD_DIR, stored)),
                uploaded_by=current_user.id
            )
    tipo_url = patrimonio.tipo.replace('_', '')
    if tipo_url == 'itemdiverso':
        tipo_url = 'item'
    return redirect(f'/inventario/{tipo_url}/{patr_id}')


@inventario_route.route('/foto-item/<int:anexo_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_foto_item(anexo_id):
    anexo = ItemAnexo.get_by_id(anexo_id)
    caminho = os.path.join(UPLOAD_DIR, anexo.stored_filename)
    if os.path.exists(caminho):
        os.remove(caminho)
    anexo.delete_instance()
    return {'deleted': 'ok'}


from . import computador, celular, telefone, impressora, item, linha


@inventario_route.route('/auditoria/<int:audit_id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_auditoria(audit_id):
    from services.equipamento_service import EquipamentoService
    auditoria = Auditoria.get_by_id(audit_id)
    service = EquipamentoService.get_for_tipo(auditoria.patrimonio.tipo)
    if not service:
        abort(404)
    return service.form_edit_auditoria(audit_id)


@inventario_route.route('/auditoria/<int:audit_id>/update', methods=['POST'])
@login_required
@admin_required
def update_auditoria(audit_id):
    from services.equipamento_service import EquipamentoService
    auditoria = Auditoria.get_by_id(audit_id)
    service = EquipamentoService.get_for_tipo(auditoria.patrimonio.tipo)
    if not service:
        abort(404)
    return service.update_auditoria(audit_id, request.form, request.files)
