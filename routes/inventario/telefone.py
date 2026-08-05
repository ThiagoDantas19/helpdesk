from flask import render_template, request, jsonify
from flask_login import login_required
from routes.auth import admin_required, tecnico_required
from utils.constants import TipoEquipamento
from utils.time import hora_local
from database.models.equipamentos import TelefoneIP, AuditoriaTelefone
from routes.inventario import inventario_route
from services.equipamento_service import EquipamentoService


service = EquipamentoService(
    model_cls=TelefoneIP,
    tipo=TipoEquipamento.TELEFONE,
    template_prefix='telefone',
    var_name='telefone',
    auditoria_cls=AuditoriaTelefone,
    auditoria_itens=['chamada_ok', 'fone_ok', 'cabo_rede_ok', 'poe_ok', 'etiqueta_legivel'],
    nome_identificador_fn=lambda d: f"Ramal {d.get('ramal')}",
    csv_header=['Data', 'Setor', 'Chamada', 'Fone', 'Cabo Rede', 'PoE', 'Etiqueta', 'Geral', 'Obs'],
    csv_row_fn=lambda a, d: _csv_row(a, d),
)


def _csv_row(a, d):
    geral = 'OK' if a.status_geral_ok else 'FALHA'
    return [
        hora_local(a.data_auditoria).strftime('%d/%m/%Y %H:%M'),
        a.setor_no_momento.nome if a.setor_no_momento else 'Sem setor',
        'OK' if d and d.chamada_ok else 'FALHA',
        'OK' if d and d.fone_ok else 'FALHA',
        'OK' if d and d.cabo_rede_ok else 'FALHA',
        'OK' if d and d.poe_ok else 'FALHA',
        'OK' if d and d.etiqueta_legivel else 'FALHA',
        geral,
        a.observacoes or ''
    ]


def _extra_create(data):
    return {
        'ramal': data.get('ramal'),
        'modelo': data.get('modelo'),
        'tag': data.get('tag'),
    }


def _extra_update(obj, data):
    obj.ramal = data.get('ramal')
    obj.modelo = data.get('modelo')
    obj.tag = data.get('tag')
    obj.save()


@inventario_route.route('/telefone/', methods=['GET'])
@login_required
@tecnico_required
def lista_telefones():
    return service.lista(page=request.args.get('page', 1, type=int))


@inventario_route.route('/telefone/new', methods=['GET'])
@login_required
@admin_required
def form_telefone():
    return render_template('inventario/telefone/form.html', **service.get_form_context())


@inventario_route.route('/telefone/', methods=['POST'])
@login_required
@admin_required
def criar_telefone():
    return service.criar(request.form, extra_fields_fn=_extra_create)


@inventario_route.route('/telefone/<int:patr_id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes_telefone(patr_id):
    return service.detalhes(patr_id)


@inventario_route.route('/telefone/<int:patr_id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_telefone(patr_id):
    return service.form_edit(patr_id)


@inventario_route.route('/telefone/<int:patr_id>/update', methods=['POST'])
@login_required
@admin_required
def update_telefone(patr_id):
    return service.atualizar(patr_id, request.form, update_fn=_extra_update)


@inventario_route.route('/telefone/<int:patr_id>/auditar', methods=['GET'])
@login_required
@tecnico_required
def form_auditoria_telefone(patr_id):
    return service.form_auditoria(patr_id)


@inventario_route.route('/telefone/<int:patr_id>/auditar', methods=['POST'])
@login_required
@admin_required
def post_auditoria_telefone(patr_id):
    return service.post_auditoria(patr_id, request.form, request.files)


@inventario_route.route('/telefone/<int:patr_id>/auditorias', methods=['GET'])
@login_required
@tecnico_required
def historico_auditorias_telefone(patr_id):
    return service.historico_auditorias(patr_id)


@inventario_route.route('/telefone/<int:patr_id>/auditorias/export', methods=['GET'])
@login_required
@tecnico_required
def export_auditorias_telefone(patr_id):
    return service.export_auditorias(patr_id)


@inventario_route.route('/telefone/<int:patr_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_telefone(patr_id):
    if service.deletar(patr_id):
        return jsonify({'deleted': 'ok'})
    return jsonify({'erro': 'Não encontrado ou falha ao excluir'}), 404
