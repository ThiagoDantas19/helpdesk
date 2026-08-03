from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from routes.auth import tecnico_required
from database.models.emprestimo import Emprestimo
from database.models.usuarios import User
from database.models.equipamentos import Patrimonio, Computador, Celular, TelefoneIP, Impressora, ItemDiverso
from database.models.log import registrar_log
from utils.time import utcnow
from datetime import datetime

emprestimo_route = Blueprint('emprestimo', __name__)


def _parse_data(data_str):
    if not data_str:
        return None
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        return False


@emprestimo_route.route('/', methods=['GET'])
@login_required
@tecnico_required
def lista():
    aberto = request.args.get('aberto', '')
    page = request.args.get('page', 1, type=int)
    por_pagina = 25

    query = Emprestimo.select().order_by(Emprestimo.data_emprestimo.desc())

    if aberto == '1':
        query = query.where(Emprestimo.data_devolucao.is_null())
    elif aberto == '0':
        query = query.where(Emprestimo.data_devolucao.is_null(False))

    total = query.count()
    pages = (total + por_pagina - 1) // por_pagina
    emprestimos = query.paginate(page, por_pagina)

    return render_template('emprestimo/lista.html',
                           emprestimos=emprestimos,
                           aberto=aberto, page=page, pages=pages, total=total)


@emprestimo_route.route('/new', methods=['GET'])
@login_required
@tecnico_required
def form():
    usuarios = User.select().where(User.ativo == True).order_by(User.nome_completo)
    com_detalhe = (Computador.select(Computador.patrimonio_id) |
                   Celular.select(Celular.patrimonio_id) |
                   TelefoneIP.select(TelefoneIP.patrimonio_id) |
                   Impressora.select(Impressora.patrimonio_id) |
                   ItemDiverso.select(ItemDiverso.patrimonio_id))
    patrimonios = Patrimonio.select().where(
        (Patrimonio.ativo == True) & (Patrimonio.id.in_(com_detalhe))
    ).order_by(Patrimonio.nome_identificador)
    return render_template('emprestimo/form.html', usuarios=usuarios, patrimonios=patrimonios)


@emprestimo_route.route('/', methods=['POST'])
@login_required
@tecnico_required
def criar():
    patrimonio_id = request.form.get('patrimonio_id', type=int)
    usuario_id = request.form.get('usuario_id', type=int)
    data_devolucao_prevista = _parse_data(request.form.get('data_devolucao_prevista'))
    observacoes = request.form.get('observacoes') or None

    if not patrimonio_id or not usuario_id:
        flash('Patrimônio e usuário são obrigatórios.', 'danger')
        return redirect('/emprestimo/new')

    if data_devolucao_prevista is False:
        flash('Data de devolução inválida. Use o formato dd/mm/aaaa.', 'danger')
        return redirect('/emprestimo/new')

    patrimonio = Patrimonio.get_by_id(patrimonio_id)
    usuario = User.get_by_id(usuario_id)

    emp = Emprestimo.create(
        patrimonio=patrimonio_id,
        usuario=usuario_id,
        responsavel=current_user.id,
        data_devolucao_prevista=data_devolucao_prevista,
        observacoes=observacoes
    )
    registrar_log(current_user, 'criar', entidade='emprestimo', entidade_id=emp.id,
                  descricao=f'Empréstimo de "{patrimonio.nome_identificador}" para {usuario.nome_completo}.')
    flash('Empréstimo registrado com sucesso.', 'success')
    return redirect('/emprestimo/')


@emprestimo_route.route('/<int:id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes(id):
    emp = Emprestimo.get_by_id(id)
    return render_template('emprestimo/det.html', emp=emp)


@emprestimo_route.route('/<int:id>/devolver', methods=['POST'])
@login_required
@tecnico_required
def devolver(id):
    emp = Emprestimo.get_by_id(id)
    if emp.data_devolucao:
        flash('Este item já foi devolvido.', 'warning')
        return redirect(f'/emprestimo/{id}')

    emp.data_devolucao = utcnow()
    emp.observacoes_devolucao = request.form.get('observacoes_devolucao') or None
    emp.save()
    registrar_log(current_user, 'atualizar', entidade='emprestimo', entidade_id=id,
                  descricao=f'Devolução de "{emp.patrimonio.nome_identificador}" registrada.')
    flash('Devolução registrada com sucesso.', 'success')
    return redirect(f'/emprestimo/{id}')


@emprestimo_route.route('/<int:id>/delete', methods=['POST'])
@login_required
@tecnico_required
def deletar(id):
    emp = Emprestimo.get_by_id(id)
    descricao = f'Empréstimo de "{emp.patrimonio.nome_identificador}" removido.'
    emp.delete_instance()
    registrar_log(current_user, 'deletar', entidade='emprestimo', entidade_id=id,
                  descricao=descricao)
    flash('Registro removido.', 'success')
    return redirect('/emprestimo/')
