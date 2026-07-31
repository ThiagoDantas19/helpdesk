from flask import render_template, request, jsonify, flash, redirect
from flask_login import login_required, current_user
from routes.auth import admin_required, tecnico_required
from database.models.equipamentos import Patrimonio, Celular, NumeroTelefone
from routes.inventario import inventario_route
from math import ceil
from database.models.log import registrar_log


@inventario_route.route('/linha/', methods=['GET'])
@login_required
@tecnico_required
def lista_linhas():
    page = int(request.args.get('page', 1))
    POR_PAGINA = 25
    query = NumeroTelefone.select()
    total = query.count()
    pages = ceil(total / POR_PAGINA)
    linhas = query.paginate(page, POR_PAGINA)
    return render_template('inventario/linha/lista.html', linhas=list(linhas), page=page, pages=pages, total=total)


@inventario_route.route('/linha/new', methods=['GET'])
@login_required
@admin_required
def form_linha():
    celulares = Celular.select().join(Patrimonio).where(Patrimonio.ativo == True)
    return render_template('inventario/linha/form.html', celulares=celulares)


@inventario_route.route('/linha/', methods=['POST'])
@login_required
@admin_required
def criar_linha():
    data = request.form
    linha = NumeroTelefone.create(
        numero=data.get('numero'),
        operadora=data.get('operadora'),
        celular=data.get('celular_id') or None,
        observacoes=data.get('observacoes')
    )
    registrar_log(current_user, 'criar', entidade='linha', entidade_id=linha.id, descricao='linha criado.')
    flash('Linha criada com sucesso.', 'success')
    return redirect('/inventario/linha/')




@inventario_route.route('/linha/<int:id>', methods=['GET'])
@login_required
@tecnico_required
def detalhes_linha(id):
    linha = NumeroTelefone.get_by_id(id)
    return render_template('inventario/linha/det.html', linha=linha)


@inventario_route.route('/linha/<int:id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_linha(id):
    linha = NumeroTelefone.get_by_id(id)
    celulares = Celular.select().join(Patrimonio).where(Patrimonio.ativo == True)
    return render_template('inventario/linha/form_edit.html', linha=linha, celulares=celulares)


@inventario_route.route('/linha/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_linha(id):
    data = request.form
    linha = NumeroTelefone.get_by_id(id)
    linha.numero = data.get('numero')
    linha.operadora = data.get('operadora')
    linha.celular = data.get('celular_id') or None
    linha.observacoes = data.get('observacoes')
    linha.save()
    registrar_log(current_user, 'atualizar', entidade='linha', entidade_id=id, descricao='linha atualizado.')
    flash('Linha atualizada com sucesso.', 'success')
    return redirect(f'/inventario/linha/{id}')


@inventario_route.route('/linha/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_linha(id):
    linha = NumeroTelefone.get_or_none(NumeroTelefone.id == id)
    if not linha:
        return jsonify({'erro': 'Linha não encontrada'}), 404
    linha.delete_instance()
    return jsonify({'deleted': 'ok'})
