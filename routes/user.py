import re
from flask import Blueprint, render_template, request, redirect, flash, jsonify
from flask_login import login_required, current_user
from routes.auth import admin_required
from database.models.usuarios import User, Setor, Cargo
from database.models.log import registrar_log
from database.database import unaccent
from peewee import fn, IntegrityError
from markupsafe import escape
from math import ceil
from datetime import datetime

user_route = Blueprint('user', __name__)
POR_PAGINA = 25


def validar_data(data_str):
    if not data_str:
        return None
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except ValueError:
        return False


def validar_email(email):
    if email is None:
        return True
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None


def _processar_email(valor):
    valor = (valor or '').strip()
    if not valor:
        return None
    return valor.lower()


@user_route.route('/', methods=['GET'])
@login_required
@admin_required
def lista_usuarios():
    nome = request.args.get('nome', '')
    setor_id = request.args.get('setor', '')
    ativo = request.args.get('ativo', '')
    vinculo = request.args.get('vinculo', '')
    page = request.args.get('page', 1, type=int)

    query = User.select().order_by(User.nome_completo)

    if nome:
        nome_norm = unaccent(nome.lower())
        query = query.where(fn.unaccent(fn.lower(User.nome_completo)).contains(nome_norm))
    if ativo != '':
        query = query.where(User.ativo == (ativo == '1'))
    if setor_id:
        query = query.where(User.setor == setor_id)
    if vinculo:
        query = query.where(User.tipo_vinculo == vinculo)

    total = query.count()
    pages = ceil(total / POR_PAGINA)
    usuarios = query.paginate(page, POR_PAGINA)
    setores = Setor.select().order_by(Setor.nome)

    return render_template('usuario/lista_usuarios_page.html',
                           usuarios=usuarios, setores=setores,
                           nome=nome, setor_id=setor_id, ativo=ativo,
                           vinculo=vinculo,
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
    if not nome_completo:
        flash('Nome completo é obrigatório.', 'danger')
        return redirect('/user/new')

    username = data.get('username', '').strip() or None
    if username and User.select().where(User.username == username).first():
        flash('Este nome de usuário já existe.', 'danger')
        return redirect('/user/new')

    email = _processar_email(data.get('email'))
    if email and not validar_email(email):
        flash('Formato de e-mail pessoal inválido.', 'danger')
        return redirect('/user/new')
    if email and User.select().where(User.email == email).first():
        flash('Este e-mail pessoal já está cadastrado.', 'danger')
        return redirect('/user/new')

    email_corp = _processar_email(data.get('email_corporativo'))
    if email_corp and not validar_email(email_corp):
        flash('Formato de e-mail corporativo inválido.', 'danger')
        return redirect('/user/new')

    data_admissao = validar_data(data.get('data_admissao'))
    if data_admissao is False:
        flash('Data de admissão inválida. Use o formato dd/mm/aaaa.', 'danger')
        return redirect('/user/new')

    setor_id = data.get('setor_id')
    cargo_id = data.get('cargo_id')
    if not setor_id or not cargo_id:
        flash('Setor e cargo são obrigatórios.', 'danger')
        return redirect('/user/new')

    try:
        user = User.create(
            nome_completo=nome_completo,
            email=email,
            username=username,
            telefone=data.get('telefone'),
            setor=setor_id,
            cargo=cargo_id,
            tipo_acesso=data.get('tipo_acesso', 'usuario'),
            tipo_vinculo=data.get('tipo_vinculo', 'efetivo'),
            data_admissao=data_admissao,
            observacoes=data.get('observacoes') or None,
            email_corporativo=email_corp,
            perfil_intelbras=data.get('perfil_intelbras'),
            acesso_ad=data.get('acesso_ad') == '1',
            acesso_sistema=data.get('acesso_sistema') == '1',
            acesso_sharepoint=data.get('acesso_sharepoint') == '1',
            biometria_dedo=data.get('biometria_dedo') == '1',
            biometria_facial=data.get('biometria_facial') == '1',
            ativo=True
        )
    except IntegrityError:
        flash('Não foi possível salvar: já existe um registro com os mesmos dados únicos.', 'danger')
        return redirect('/user/new')

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

    email = _processar_email(data.get('email'))
    if email and not validar_email(email):
        flash('Formato de e-mail pessoal inválido.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    if email and User.select().where(User.email == email, User.id != user_id).first():
        flash('Este e-mail pessoal já está em uso por outro usuário.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    usuario.email = email

    username = data.get('username', '').strip() or None
    if username and User.select().where(User.username == username, User.id != user_id).first():
        flash('Este nome de usuário já está em uso.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    usuario.username = username
    usuario.telefone = data.get('telefone')
    setor_id = data.get('setor_id')
    cargo_id = data.get('cargo_id')
    if not setor_id or not cargo_id:
        flash('Setor e cargo são obrigatórios.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    usuario.setor = setor_id
    usuario.cargo = cargo_id
    usuario.tipo_acesso = data.get('tipo_acesso')
    usuario.tipo_vinculo = data.get('tipo_vinculo')

    email_corp = _processar_email(data.get('email_corporativo'))
    if email_corp and not validar_email(email_corp):
        flash('Formato de e-mail corporativo inválido.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    usuario.email_corporativo = email_corp

    usuario.perfil_intelbras = data.get('perfil_intelbras')
    usuario.observacoes = data.get('observacoes') or None
    data_admissao = validar_data(data.get('data_admissao'))
    data_desligamento = validar_data(data.get('data_desligamento'))
    if data_admissao is False or data_desligamento is False:
        flash('Data inválida. Use o formato dd/mm/aaaa.', 'danger')
        return redirect(f'/user/{user_id}/edit')
    usuario.data_admissao = data_admissao
    usuario.data_desligamento = data_desligamento
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

    try:
        usuario.save()
    except IntegrityError:
        flash('Não foi possível salvar: já existe um registro com os mesmos dados únicos.', 'danger')
        return redirect(f'/user/{user_id}/edit')

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
