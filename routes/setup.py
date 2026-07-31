from flask import Blueprint, render_template, request, redirect, flash
from database.seed import popular_setores_e_cargos
from database.models.usuarios import User, Setor, Cargo

setup_route = Blueprint('setup', __name__)


@setup_route.before_app_request
def check_setup():
    if request.method != 'GET':
        return
    if request.path.startswith(('/setup/', '/static/')):
        return
    if request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return
    try:
        if User.select().count() == 0:
            return redirect('/setup/')
    except Exception:
        pass


@setup_route.route('/setup/', methods=['GET'])
def setup():
    try:
        if User.select().count() > 0:
            return redirect('/')
    except Exception:
        pass
    return render_template('setup.html')


@setup_route.route('/setup/seed', methods=['POST'])
def seed():
    try:
        if User.select().count() > 0:
            return redirect('/')
    except Exception:
        pass

    popular_setores_e_cargos()

    nome_completo = request.form.get('nome_completo', '').strip()
    email = request.form.get('email', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not all([nome_completo, email, username, password]):
        flash('Preencha todos os campos.', 'danger')
        return render_template('setup.html')

    setor = Setor.select().first()
    cargo = Cargo.select().where(Cargo.setor == setor).first() if setor else None

    if not setor or not cargo:
        flash('Erro ao configurar: setores/cargos não encontrados. Tente novamente.', 'danger')
        return redirect('/setup/')

    admin = User.create(
        nome_completo=nome_completo,
        email=email,
        username=username,
        tipo_acesso='admin',
        setor=setor,
        cargo=cargo,
        ativo=True
    )
    admin.set_password(password)
    admin.save()

    flash('Sistema configurado! Faça login para continuar.', 'success')
    return redirect('/login')
