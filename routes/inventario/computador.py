from flask import request, render_template, jsonify
from flask_login import login_required, current_user
from routes.auth import admin_required, tecnico_required
from utils.constants import TipoEquipamento
from database.models.equipamentos import Computador, AuditoriaComputador
from routes.inventario import inventario_route
from services.equipamento_service import EquipamentoService
from datetime import datetime


def _parse_data(data_str):
    if not data_str:
        return None
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        return False


service = EquipamentoService(
    model_cls=Computador,
    tipo=TipoEquipamento.COMPUTADOR,
    template_prefix='computador',
    var_name='computador',
    var_name_plural='computadores',
    auditoria_cls=AuditoriaComputador,
    auditoria_itens=[
        'hardware_integro', 'bateria_ok', 'perifericos_ok', 'limpeza_fisica_ok',
        'antivirus_ok', 'criptografia_ok', 'updates_ok', 'softwares_ok',
        'dominio_ok', 'vpn_ok', 'limpeza_disco_ok',
        'alocacao_ok', 'etiqueta_legivel'
    ],
    nome_identificador_fn=lambda d: d.get('nome_identificador'),
    csv_header=[
        'Data', 'Setor',
        'Hardware', 'Bateria', 'Perifericos', 'Limpeza',
        'Antivirus', 'Criptografia', 'Updates', 'Softwares',
        'Dominio', 'VPN', 'Limpeza Disco',
        'Alocacao', 'Etiqueta', 'Geral', 'Obs'
    ],
    csv_row_fn=lambda a, d: _csv_row(a, d),
)


def _csv_row(a, d):
    geral = 'OK' if a.status_geral_ok else 'FALHA'
    return [
        a.data_auditoria.strftime('%d/%m/%Y %H:%M'),
        a.setor_no_momento.nome if a.setor_no_momento else 'Sem setor',
        'OK' if d and d.hardware_integro else 'FALHA',
        'OK' if d and d.bateria_ok else 'FALHA',
        'OK' if d and d.perifericos_ok else 'FALHA',
        'OK' if d and d.limpeza_fisica_ok else 'FALHA',
        'OK' if d and d.antivirus_ok else 'FALHA',
        'OK' if d and d.criptografia_ok else 'FALHA',
        'OK' if d and d.updates_ok else 'FALHA',
        'OK' if d and d.softwares_ok else 'FALHA',
        'OK' if d and d.dominio_ok else 'FALHA',
        'OK' if d and d.vpn_ok else 'FALHA',
        'OK' if d and d.limpeza_disco_ok else 'FALHA',
        'OK' if d and d.alocacao_ok else 'FALHA',
        'OK' if d and d.etiqueta_legivel else 'FALHA',
        geral,
        a.observacoes or ''
    ]


def _extra_create(data):
    data_fabricacao = _parse_data(data.get('data_fabricacao'))
    if data_fabricacao is False:
        raise ValueError('Data de fabricação inválida. Use o formato dd/mm/aaaa.')
    return {
        'tag': data.get('tag'),
        'nome_ad': data.get('nome_ad'),
        'numero_serie': data.get('numero_serie'),
        'data_fabricacao': data_fabricacao,
    }


def _extra_update(obj, data):
    data_fabricacao = _parse_data(data.get('data_fabricacao'))
    if data_fabricacao is False:
        raise ValueError('Data de fabricação inválida. Use o formato dd/mm/aaaa.')
    obj.tag = data.get('tag')
    obj.nome_ad = data.get('nome_ad')
    obj.numero_serie = data.get('numero_serie')
    obj.data_fabricacao = data_fabricacao
    obj.save()


@inventario_route.route('/computador/', methods=['GET'])
@login_required
@tecnico_required
def lista_computadores():
    return service.lista(page=request.args.get('page', 1, type=int))


@inventario_route.route('/computador/new', methods=['GET'])
@login_required
@admin_required
def form_computador():
    return render_template('inventario/computador/form.html', **service.get_form_context())


@inventario_route.route('/computador/', methods=['POST'])
@login_required
@admin_required
def criar_computador():
    return service.criar(request.form, extra_fields_fn=_extra_create)


@inventario_route.route('/computador/<int:patr_id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes_computador(patr_id):
    return service.detalhes(patr_id)


@inventario_route.route('/computador/<int:patr_id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_computador(patr_id):
    return service.form_edit(patr_id)


@inventario_route.route('/computador/<int:patr_id>/update', methods=['POST'])
@login_required
@admin_required
def update_computador(patr_id):
    return service.atualizar(patr_id, request.form, update_fn=_extra_update)


@inventario_route.route('/computador/<int:patr_id>/auditar', methods=['GET'])
@login_required
@tecnico_required
def form_auditoria_computador(patr_id):
    return service.form_auditoria(patr_id)


@inventario_route.route('/computador/<int:patr_id>/auditar', methods=['POST'])
@login_required
@admin_required
def post_auditoria_computador(patr_id):
    return service.post_auditoria(patr_id, request.form, request.files)


@inventario_route.route('/computador/<int:patr_id>/auditorias', methods=['GET'])
@login_required
@tecnico_required
def historico_auditorias_computador(patr_id):
    return service.historico_auditorias(patr_id)


@inventario_route.route('/computador/<int:patr_id>/auditorias/export', methods=['GET'])
@login_required
@tecnico_required
def export_auditorias_computador(patr_id):
    return service.export_auditorias(patr_id)


@inventario_route.route('/computador/<int:patr_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_computador(patr_id):
    if service.deletar(patr_id):
        return jsonify({'deleted': 'ok'})
    return jsonify({'erro': 'Não encontrado ou falha ao excluir'}), 404
