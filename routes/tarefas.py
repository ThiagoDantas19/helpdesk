from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database.models.tarefa import Tarefa
from utils.time import hora_local
from datetime import date, datetime
import calendar

calendar.setfirstweekday(calendar.SUNDAY)

tarefas_route = Blueprint('tarefas', __name__)

MESES_PT = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


@tarefas_route.route('/api/tarefas', methods=['GET'])
@login_required
def listar():
    tarefas = (Tarefa.select()
               .where(Tarefa.usuario == current_user.id)
               .order_by(Tarefa.concluida, Tarefa.criado_em.desc()))
    return jsonify([{
        'id': t.id,
        'titulo': t.titulo,
        'concluida': t.concluida,
        'data_vencimento': t.data_vencimento.isoformat() if t.data_vencimento else None,
        'criado_em': hora_local(t.criado_em).isoformat()
    } for t in tarefas])


@tarefas_route.route('/api/tarefas', methods=['POST'])
@login_required
def criar():
    data = request.get_json(silent=True) or request.form
    titulo = data.get('titulo', '').strip()
    if not titulo:
        return jsonify({'erro': 'Título é obrigatório'}), 400
    vencimento = data.get('data_vencimento')
    if vencimento:
        try:
            vencimento = datetime.strptime(vencimento, '%d/%m/%Y').date()
        except ValueError:
            try:
                vencimento = date.fromisoformat(vencimento)
            except (ValueError, TypeError):
                return jsonify({'erro': 'Data inválida. Use o formato dd/mm/aaaa'}), 400
    tarefa = Tarefa.create(usuario=current_user.id, titulo=titulo, data_vencimento=vencimento)
    return jsonify({
        'id': tarefa.id,
        'titulo': tarefa.titulo,
        'concluida': False,
        'data_vencimento': tarefa.data_vencimento.isoformat() if tarefa.data_vencimento else None
    }), 201


@tarefas_route.route('/api/tarefas/<int:tarefa_id>/toggle', methods=['POST'])
@login_required
def toggle(tarefa_id):
    tarefa = Tarefa.get_or_none(Tarefa.id == tarefa_id, Tarefa.usuario == current_user.id)
    if not tarefa:
        return jsonify({'erro': 'Tarefa não encontrada'}), 404
    tarefa.concluida = not tarefa.concluida
    tarefa.save()
    return jsonify({'id': tarefa.id, 'concluida': tarefa.concluida})


@tarefas_route.route('/api/tarefas/<int:tarefa_id>', methods=['DELETE'])
@login_required
def deletar(tarefa_id):
    tarefa = Tarefa.get_or_none(Tarefa.id == tarefa_id, Tarefa.usuario == current_user.id)
    if not tarefa:
        return jsonify({'erro': 'Tarefa não encontrada'}), 404
    tarefa.delete_instance()
    return jsonify({'ok': True})


@tarefas_route.route('/api/tarefas/calendario', methods=['GET'])
@login_required
def calendario():
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', type=int)

    hoje_ano = request.args.get('hoje_ano', type=int)
    hoje_mes = request.args.get('hoje_mes', type=int)
    hoje_dia = request.args.get('hoje_dia', type=int)

    if hoje_ano and hoje_mes and hoje_dia:
        hoje = date(hoje_ano, hoje_mes, hoje_dia)
    else:
        hoje = date.today()

    mes = mes or hoje.month
    ano = ano or hoje.year

    cal = calendar.monthcalendar(ano, mes)
    nome_mes = MESES_PT[mes]

    tarefas = (Tarefa.select()
               .where(
                   Tarefa.usuario == current_user.id,
                   Tarefa.data_vencimento.is_null(False),
                   Tarefa.concluida == False
               ))
    dots = {}
    for t in tarefas:
        d = t.data_vencimento
        chave = f'{d.year}-{d.month:02d}-{d.day:02d}'
        dots[chave] = dots.get(chave, 0) + 1

    return jsonify({
        'ano': ano,
        'mes': mes,
        'nome_mes': nome_mes,
        'semanas': cal,
        'hoje': hoje.day,
        'hoje_mes': hoje.month,
        'hoje_ano': hoje.year,
        'dots': dots,
        'total_pendentes': Tarefa.select().where(
            Tarefa.usuario == current_user.id,
            Tarefa.concluida == False
        ).count()
    })
