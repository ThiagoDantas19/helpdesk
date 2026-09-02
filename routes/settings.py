from flask import Blueprint, render_template, request, redirect, flash, jsonify, current_app
from flask_login import login_required, current_user
from routes.auth import admin_required
from database.models.usuarios import Setor, Cargo, User
from database.models.log import registrar_log
from database.models.credencial import Credencial
from utils.crypto import encrypt, decrypt
from utils.cache import invalidate as cache_invalidate
from utils.time import utcnow

settings_route = Blueprint('settings', __name__)


@settings_route.route('/', methods=['GET'])
@login_required
@admin_required
def hub():
    return render_template('settings/hub.html')


@settings_route.route('/setor/', methods=['GET'])
@login_required
@admin_required
def lista_setores():
    setores = Setor.select().order_by(Setor.nome)
    return render_template('settings/setores.html', setores=setores)


@settings_route.route('/setor/new', methods=['GET'])
@login_required
@admin_required
def form_setor():
    return render_template('settings/form_setor.html')


@settings_route.route('/setor/', methods=['POST'])
@login_required
@admin_required
def criar_setor():
    nome = request.form.get('nome', '').strip()
    if nome:
        setor, _ = Setor.get_or_create(nome=nome)
        registrar_log(current_user, 'criar', entidade='setor', entidade_id=setor.id,
                      descricao=f'Setor "{nome}" criado.')
        cache_invalidate('setores_ordenados')
        flash(f'Setor "{nome}" criado com sucesso.', 'success')
    return redirect('/settings/setor/')


@settings_route.route('/setor/<int:id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_setor(id):
    setor = Setor.get_by_id(id)
    return render_template('settings/form_setor.html', setor=setor)


@settings_route.route('/setor/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_setor(id):
    setor = Setor.get_by_id(id)
    setor.nome = request.form.get('nome', '').strip()
    setor.save()
    registrar_log(current_user, 'atualizar', entidade='setor', entidade_id=id,
                  descricao=f'Setor atualizado para "{setor.nome}".')
    cache_invalidate('setores_ordenados')
    flash(f'Setor atualizado.', 'success')
    return redirect('/settings/setor/')


@settings_route.route('/setor/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_setor(id):
    setor = Setor.get_by_id(id)
    if User.select().where(User.setor == id).first():
        return jsonify({'error': 'Não é possível excluir: existem usuários neste setor.'}), 409
    nome = setor.nome
    setor.delete_instance()
    registrar_log(current_user, 'deletar', entidade='setor', entidade_id=id,
                  descricao=f'Setor "{nome}" deletado.')
    cache_invalidate('setores_ordenados')
    return jsonify({'deleted': 'ok'})


@settings_route.route('/cargo/', methods=['GET'])
@login_required
@admin_required
def lista_cargos():
    setor_id = request.args.get('setor_id', type=int)
    query = Cargo.select(Cargo, Setor).join(Setor).order_by(Setor.nome, Cargo.nome)
    if setor_id:
        query = query.where(Cargo.setor == setor_id)
    cargos = query
    setores = Setor.select().order_by(Setor.nome)
    return render_template('settings/cargos.html', cargos=cargos, setores=setores, setor_id=setor_id)


@settings_route.route('/cargo/new', methods=['GET'])
@login_required
@admin_required
def form_cargo():
    setores = Setor.select().order_by(Setor.nome)
    return render_template('settings/form_cargo.html', setores=setores)


@settings_route.route('/cargo/', methods=['POST'])
@login_required
@admin_required
def criar_cargo():
    nome = request.form.get('nome', '').strip()
    setor_id = request.form.get('setor_id', type=int)
    if nome and setor_id:
        cargo = Cargo.create(nome=nome, setor=setor_id)
        registrar_log(current_user, 'criar', entidade='cargo', entidade_id=cargo.id,
                      descricao=f'Cargo "{nome}" criado.')
        flash(f'Cargo "{nome}" criado com sucesso.', 'success')
    return redirect('/settings/cargo/')


@settings_route.route('/cargo/<int:id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_cargo(id):
    cargo = Cargo.get_by_id(id)
    setores = Setor.select().order_by(Setor.nome)
    return render_template('settings/form_cargo.html', cargo=cargo, setores=setores)


@settings_route.route('/cargo/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_cargo(id):
    cargo = Cargo.get_by_id(id)
    cargo.nome = request.form.get('nome', '').strip()
    cargo.setor = request.form.get('setor_id', type=int) or cargo.setor
    cargo.save()
    registrar_log(current_user, 'atualizar', entidade='cargo', entidade_id=id,
                  descricao=f'Cargo atualizado para "{cargo.nome}".')
    flash(f'Cargo atualizado.', 'success')
    return redirect('/settings/cargo/')


@settings_route.route('/cargo/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_cargo(id):
    cargo = Cargo.get_by_id(id)
    if User.select().where(User.cargo == id).first():
        return jsonify({'error': 'Não é possível excluir: existem usuários com este cargo.'}), 409
    nome = cargo.nome
    cargo.delete_instance()
    registrar_log(current_user, 'deletar', entidade='cargo', entidade_id=id,
                  descricao=f'Cargo "{nome}" deletado.')
    return jsonify({'deleted': 'ok'})


@settings_route.route('/credencial/', methods=['GET'])
@login_required
@admin_required
def lista_credenciais():
    credenciais = Credencial.select().order_by(Credencial.titulo)
    return render_template('settings/credenciais.html', credenciais=credenciais)


@settings_route.route('/credencial/new', methods=['GET'])
@login_required
@admin_required
def form_credencial():
    return render_template('settings/form_credencial.html')


@settings_route.route('/credencial/', methods=['POST'])
@login_required
@admin_required
def criar_credencial():
    titulo = request.form.get('titulo', '').strip()
    username = request.form.get('username', '').strip()
    senha_plana = request.form.get('senha', '').strip()
    url = request.form.get('url', '').strip() or None
    observacao = request.form.get('observacao', '').strip() or None

    if not titulo or not username or not senha_plana:
        flash('Título, usuário e senha são obrigatórios.', 'danger')
        return redirect('/settings/credencial/new')

    senha_enc = encrypt(senha_plana, current_app.config['SECRET_KEY'])

    c = Credencial.create(
        titulo=titulo, url=url, username=username,
        senha=senha_enc, observacao=observacao,
        created_by=current_user.id
    )
    registrar_log(current_user, 'criar', entidade='credencial', entidade_id=c.id,
                  descricao=f'Credencial "{titulo}" criada.')
    flash(f'Credencial "{titulo}" criada com sucesso.', 'success')
    return redirect('/settings/credencial/')


@settings_route.route('/credencial/<int:id>/edit', methods=['GET'])
@login_required
@admin_required
def edit_credencial(id):
    c = Credencial.get_by_id(id)
    return render_template('settings/form_credencial.html', credencial=c)


@settings_route.route('/credencial/<int:id>/update', methods=['POST'])
@login_required
@admin_required
def update_credencial(id):
    c = Credencial.get_by_id(id)
    c.titulo = request.form.get('titulo', '').strip()
    c.username = request.form.get('username', '').strip()
    c.url = request.form.get('url', '').strip() or None
    c.observacao = request.form.get('observacao', '').strip() or None

    senha_plana = request.form.get('senha', '').strip()
    if senha_plana:
        c.senha = encrypt(senha_plana, current_app.config['SECRET_KEY'])

    c.updated_at = utcnow()
    c.save()
    registrar_log(current_user, 'atualizar', entidade='credencial', entidade_id=id,
                  descricao=f'Credencial "{c.titulo}" atualizada.')
    flash(f'Credencial atualizada.', 'success')
    return redirect('/settings/credencial/')


@settings_route.route('/credencial/<int:id>/reveal', methods=['POST'])
@login_required
@admin_required
def revelar_senha(id):
    c = Credencial.get_by_id(id)
    senha = decrypt(c.senha, current_app.config['SECRET_KEY'])
    return jsonify({'senha': senha or ''})


@settings_route.route('/credencial/<int:id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_credencial(id):
    c = Credencial.get_by_id(id)
    titulo = c.titulo
    c.delete_instance()
    registrar_log(current_user, 'deletar', entidade='credencial', entidade_id=id,
                  descricao=f'Credencial "{titulo}" deletada.')
    return jsonify({'deleted': 'ok'})
