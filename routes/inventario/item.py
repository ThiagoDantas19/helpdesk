from flask import render_template, request, jsonify
from flask_login import login_required
from routes.auth import admin_required, tecnico_required
from utils.constants import TipoEquipamento
from utils.time import hora_local
from database.models.equipamentos import ItemDiverso, AuditoriaItemDiverso
from routes.inventario import inventario_route
from services.equipamento_service import EquipamentoService


service = EquipamentoService(
    model_cls=ItemDiverso,
    tipo=TipoEquipamento.ITEM_DIVERSO,
    template_prefix='item',
    var_name='item',
    var_name_plural='itens',
    auditoria_cls=AuditoriaItemDiverso,
    auditoria_itens=['estado_fisico_ok', 'funcionamento_ok', 'acessorios_ok', 'etiqueta_legivel'],
    nome_identificador_fn=lambda d: d.get('nome'),
    csv_header=['Data', 'Setor', 'Estado Fisico', 'Funcionamento', 'Acessorios', 'Etiqueta', 'Geral', 'Obs'],
    csv_row_fn=lambda a, d: _csv_row(a, d),
)


def _csv_row(a, d):
    geral = 'OK' if a.status_geral_ok else 'FALHA'
    return [
        hora_local(a.data_auditoria).strftime('%d/%m/%Y %H:%M'),
        a.setor_no_momento.nome if a.setor_no_momento else 'Sem setor',
        'OK' if d and d.estado_fisico_ok else 'FALHA',
        'OK' if d and d.funcionamento_ok else 'FALHA',
        'OK' if d and d.acessorios_ok else 'FALHA',
        'OK' if d and d.etiqueta_legivel else 'FALHA',
        geral,
        a.observacoes or ''
    ]


def _extra_create(data):
    return {
        'nome': data.get('nome'),
        'tipo_item': data.get('tipo_item'),
        'numero_serie': data.get('numero_serie'),
    }


def _extra_update(obj, data):
    obj.nome = data.get('nome')
    obj.tipo_item = data.get('tipo_item')
    obj.numero_serie = data.get('numero_serie')
    obj.save()


@inventario_route.route('/item/', methods=['GET'])
@login_required
@tecnico_required
def lista_itens_diversos():
    return service.lista(page=request.args.get('page', 1, type=int))


@inventario_route.route('/item/new', methods=['GET'])
@login_required
@admin_required
def form_item_diverso():
    return render_template('inventario/item/form.html', **service.get_form_context())


@inventario_route.route('/item/', methods=['POST'])
@login_required
@admin_required
def criar_item_diverso():
    return service.criar(request.form, extra_fields_fn=_extra_create)


@inventario_route.route('/item/<int:patr_id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes_item_diverso(patr_id):
    from database.models.chamados import ChamadoEquipamento
    filtro = (ChamadoEquipamento.tipo_equipamento == TipoEquipamento.ITEM_DIVERSO.value)
    return service.detalhes(patr_id, chamado_filtro_extra=filtro)


@inventario_route.route('/item/<int:patr_id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_item_diverso(patr_id):
    return service.form_edit(patr_id)


@inventario_route.route('/item/<int:patr_id>/update', methods=['POST'])
@login_required
@admin_required
def update_item_diverso(patr_id):
    return service.atualizar(patr_id, request.form, update_fn=_extra_update)


@inventario_route.route('/item/<int:patr_id>/auditar', methods=['GET'])
@login_required
@tecnico_required
def form_auditoria_item(patr_id):
    return service.form_auditoria(patr_id)


@inventario_route.route('/item/<int:patr_id>/auditar', methods=['POST'])
@login_required
@admin_required
def post_auditoria_item(patr_id):
    return service.post_auditoria(patr_id, request.form, request.files)


@inventario_route.route('/item/<int:patr_id>/auditorias', methods=['GET'])
@login_required
@tecnico_required
def historico_auditorias_item(patr_id):
    return service.historico_auditorias(patr_id)


@inventario_route.route('/item/<int:patr_id>/auditorias/export', methods=['GET'])
@login_required
@tecnico_required
def export_auditorias_item(patr_id):
    return service.export_auditorias(patr_id)


@inventario_route.route('/item/<int:patr_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_item(patr_id):
    if service.deletar(patr_id):
        return jsonify({'deleted': 'ok'})
    return jsonify({'erro': 'Não encontrado ou falha ao excluir'}), 404
