from flask import render_template, request, jsonify
from flask_login import login_required
from routes.auth import admin_required, tecnico_required
from utils.constants import TipoEquipamento
from database.models.equipamentos import Impressora, AuditoriaImpressora
from routes.inventario import inventario_route
from services.equipamento_service import EquipamentoService


service = EquipamentoService(
    model_cls=Impressora,
    tipo=TipoEquipamento.IMPRESSORA,
    template_prefix='impressora',
    var_name='impressora',
    auditoria_cls=AuditoriaImpressora,
    auditoria_itens=['liga_ok', 'qualidade_impressao_ok', 'scanner_ok', 'nivel_suprimentos_ok', 'cabos_ok'],
    nome_identificador_fn=lambda d: f"{d.get('marca')} {d.get('modelo')}",
    csv_header=['Data', 'Setor', 'Liga', 'Qualidade', 'Scanner', 'Suprimentos', 'Cabos', 'Geral', 'Obs'],
    csv_row_fn=lambda a, d: _csv_row(a, d),
)


def _csv_row(a, d):
    geral = 'OK' if a.status_geral_ok else 'FALHA'
    return [
        a.data_auditoria.strftime('%d/%m/%Y %H:%M'),
        a.setor_no_momento.nome if a.setor_no_momento else 'Sem setor',
        'OK' if d and d.liga_ok else 'FALHA',
        'OK' if d and d.qualidade_impressao_ok else 'FALHA',
        'OK' if d and d.scanner_ok else 'FALHA',
        'OK' if d and d.nivel_suprimentos_ok else 'FALHA',
        'OK' if d and d.cabos_ok else 'FALHA',
        geral,
        a.observacoes or ''
    ]


def _extra_create(data):
    return {
        'marca': data.get('marca'),
        'modelo': data.get('modelo'),
        'numero_serie': data.get('numero_serie'),
    }


def _extra_update(obj, data):
    obj.marca = data.get('marca')
    obj.modelo = data.get('modelo')
    obj.numero_serie = data.get('numero_serie')
    obj.save()


@inventario_route.route('/impressora/', methods=['GET'])
@login_required
@tecnico_required
def lista_impressoras():
    return service.lista(page=request.args.get('page', 1, type=int))


@inventario_route.route('/impressora/new', methods=['GET'])
@login_required
@admin_required
def form_impressora():
    return render_template('inventario/impressora/form.html', **service.get_form_context())


@inventario_route.route('/impressora/', methods=['POST'])
@login_required
@admin_required
def criar_impressora():
    return service.criar(request.form, extra_fields_fn=_extra_create)


@inventario_route.route('/impressora/<int:patr_id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes_impressora(patr_id):
    from database.models.chamados import ChamadoEquipamento
    filtro = (ChamadoEquipamento.tipo_equipamento == TipoEquipamento.IMPRESSORA.value)
    return service.detalhes(patr_id, chamado_filtro_extra=filtro)


@inventario_route.route('/impressora/<int:patr_id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_impressora(patr_id):
    return service.form_edit(patr_id)


@inventario_route.route('/impressora/<int:patr_id>/update', methods=['POST'])
@login_required
@admin_required
def update_impressora(patr_id):
    return service.atualizar(patr_id, request.form, update_fn=_extra_update)


@inventario_route.route('/impressora/<int:patr_id>/auditar', methods=['GET'])
@login_required
@tecnico_required
def form_auditoria_impressora(patr_id):
    return service.form_auditoria(patr_id)


@inventario_route.route('/impressora/<int:patr_id>/auditar', methods=['POST'])
@login_required
@admin_required
def post_auditoria_impressora(patr_id):
    return service.post_auditoria(patr_id, request.form, request.files)


@inventario_route.route('/impressora/<int:patr_id>/auditorias', methods=['GET'])
@login_required
@tecnico_required
def historico_auditorias_impressora(patr_id):
    return service.historico_auditorias(patr_id)


@inventario_route.route('/impressora/<int:patr_id>/auditorias/export', methods=['GET'])
@login_required
@tecnico_required
def export_auditorias_impressora(patr_id):
    return service.export_auditorias(patr_id)


@inventario_route.route('/impressora/<int:patr_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_impressora(patr_id):
    if service.deletar(patr_id):
        return jsonify({'deleted': 'ok'})
    return jsonify({'erro': 'Não encontrado ou falha ao excluir'}), 404
