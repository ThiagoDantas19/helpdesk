from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from routes.auth import admin_required
from database.models.usuarios import User, Setor, Cargo
from database.models.log import registrar_log
from markupsafe import escape
from math import ceil

user_route = Blueprint('user', __name__)
POR_PAGINA = 25


@user_route.route('/', methods=['GET'])
@login_required
@admin_required
def lista_usuarios():
    nome = request.args.get('nome', '')
    setor_id = request.args.get('setor', '')
    ativo = request.args.get('ativo', '')
    page = request.args.get('page', 1, type=int)

    query = User.select().order_by(User.nome_completo)

    if nome:
        query = query.where(User.nome_completo.contains(nome))
    if ativo != '':
        query = query.where(User.ativo == (ativo == '1'))
    if setor_id:
        query = query.where(User.setor == setor_id)

    total = query.count()
    pages = ceil(total / POR_PAGINA)
    usuarios = query.paginate(page, POR_PAGINA)
    setores = Setor.select().order_by(Setor.nome)

    return render_template('usuario/lista_usuarios_page.html',
                           usuarios=usuarios, setores=setores,
                           nome=nome, setor_id=setor_id, ativo=ativo,
                           page=page, pages=pages, total=total)


@user_route.route('/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def detalhes_usuario(user_id):
    usuario = User.get_by_id(user_id)
    return render_template('usuario/det_usuario.html', usuario=usuario)


@user_route.route('/new', methods=['GET'])
@login_required
@admin_required
def form_usuario():
    setores = Setor.select().order_by(Setor.nome)
    return render_template('usuario/form_usuario.html', setores=setores)


@user_route.route('/', methods=['POST'])
@login_required
@admin_required
def criar_usuario():
    data = request.form

    nome_completo = data.get('nome_completo', '').strip()
    email = data.get('email', '').strip() or None
    if not nome_completo:
        flash('Nome completo é obrigatório.', 'danger')
        return redirect('/user/new')

    username = data.get('username', '').strip() or None
    if username and User.select().where(User.username == username).first():
        flash('Este nome de usuário já existe.', 'danger')
        return redirect('/user/new')

    user = User.create(
        nome_completo=nome_completo,
        email=email,
        username=username,
        telefone=data.get('telefone'),
        setor=data.get('setor_id'),
        cargo=data.get('cargo_id'),
        tipo_acesso=data.get('tipo_acesso', 'usuario'),
        tipo_vinculo=data.get('tipo_vinculo', 'efetivo'),
        data_admissao=data.get('data_admissao') or None,
        observacoes=data.get('observacoes') or None,
        email_corporativo=data.get('email_corporativo'),
        perfil_intelbras=data.get('perfil_intelbras'),
        acesso_ad=data.get('acesso_ad') == '1',
        acesso_sistema=data.get('acesso_sistema') == '1',
        acesso_sharepoint=data.get('acesso_sharepoint') == '1',
        biometria_dedo=data.get('biometria_dedo') == '1',
        biometria_facial=data.get('biometria_facial') == '1',
        ativo=True
    )
    password = data.get('password')
    if password:
        if len(password) < 4:
            flash('A senha deve ter no mínimo 4 caracteres.', 'danger')
            return redirect('/user/new')
        user.set_password(password)
        user.save()
    registrar_log(current_user, 'criar', entidade='user', entidade_id=user.id,
                  descricao=f'Usuário {user.username} criado.')
    flash('Usuário criado com sucesso.', 'success')
    return redirect('/user/')


@user_route.route('/<int:user_id>/edit', methods=['GET'])
@login_required
@admin_required
def form_edit_usuario(user_id):
    usuario = User.get_by_id(user_id)
    setores = Setor.select().order_by(Setor.nome)
    cargos = Cargo.select().where(Cargo.setor == usuario.setor).order_by(Cargo.nome)
    return render_template('usuario/form_edit_usuario.html',
                           usuario=usuario, setores=setores, cargos=cargos)


@user_route.route('/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_usuario(user_id):
    usuario = User.get_by_id(user_id)
    data = request.form

    usuario.nome_completo = data.get('nome_completo')
    usuario.email = data.get('email', '').strip() or None
    username = data.get('username', '').strip() or None
    if username and User.select().where(User.username == username, User.id != user_id).first():
        flash('Este nome de usuário já está em uso.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    usuario.username = username
    usuario.telefone = data.get('telefone')
    usuario.setor = data.get('setor_id')
    usuario.cargo = data.get('cargo_id')
    usuario.tipo_acesso = data.get('tipo_acesso')
    usuario.tipo_vinculo = data.get('tipo_vinculo')
    usuario.email_corporativo = data.get('email_corporativo')
    usuario.perfil_intelbras = data.get('perfil_intelbras')
    usuario.observacoes = data.get('observacoes') or None
    usuario.data_admissao = data.get('data_admissao') or None
    usuario.data_desligamento = data.get('data_desligamento') or None
    usuario.ativo = data.get('ativo') == '1'

    usuario.acesso_ad = data.get('acesso_ad') == '1'
    usuario.acesso_sistema = data.get('acesso_sistema') == '1'
    usuario.acesso_sharepoint = data.get('acesso_sharepoint') == '1'
    usuario.biometria_dedo = data.get('biometria_dedo') == '1'
    usuario.biometria_facial = data.get('biometria_facial') == '1'

    password = data.get('password')
    if password:
        if len(password) < 4:
            flash('A senha deve ter no mínimo 4 caracteres.', 'danger')
            return redirect(f'/user/{user_id}/edit')
        usuario.set_password(password)

    usuario.save()
    registrar_log(current_user, 'atualizar', entidade='user', entidade_id=usuario.id,
                  descricao=f'Usuário {usuario.username} atualizado.')
    flash('Usuário atualizado com sucesso.', 'success')
    return redirect('/user/')


@user_route.route('/buscar-cargos', methods=['GET'])
@login_required
@admin_required
def buscar_cargos():
    setor_id = request.args.get('setor_id')
    if not setor_id:
        return '<option value="">Selecione o setor primeiro...</option>'

    cargos = Cargo.select().where(Cargo.setor == setor_id).order_by(Cargo.nome)
    html_options = '<option value="">Selecione o cargo...</option>'
    for c in cargos:
        html_options += f'<option value="{c.id}">{escape(c.nome)}</option>'
    return html_options


@user_route.route('/verificar-username', methods=['GET'])
@login_required
@admin_required
def verificar_username():
    username = request.args.get('username', '').strip()
    excluir = request.args.get('excluir', type=int)
    if not username:
        return jsonify({'disponivel': True})
    query = User.select().where(User.username == username)
    if excluir:
        query = query.where(User.id != excluir)
    existe = query.first() is not None
    return jsonify({'disponivel': not existe})


@user_route.route('/<int:user_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def deletar_usuario(user_id):
    if user_id == current_user.id:
        return jsonify({'deleted': 'error', 'message': 'Você não pode excluir a si mesmo.'}), 400
    usuario = User.get_by_id(user_id)
    username = usuario.username
    usuario.delete_instance()
    registrar_log(current_user, 'deletar', entidade='user', entidade_id=user_id,
                  descricao=f'Usuário {username} deletado.')
    return jsonify({'deleted': 'ok'})
