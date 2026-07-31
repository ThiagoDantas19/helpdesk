import time
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from flask_login import login_user, logout_user, current_user
from database.models.usuarios import User
from database.models.log import registrar_log
from utils.time import utcnow
from utils.constants import TipoAcesso

auth_route = Blueprint('auth', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.tipo_acesso != TipoAcesso.ADMIN.value:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def tecnico_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.tipo_acesso not in (TipoAcesso.ADMIN.value, TipoAcesso.TECNICO.value):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def pode_ver_chamado(chamado):
    if current_user.tipo_acesso == TipoAcesso.ADMIN.value:
        return True
    if current_user.tipo_acesso == TipoAcesso.TECNICO.value:
        return True
    return chamado.funcionario.id == current_user.id


@auth_route.route('/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('login.html')


@auth_route.route('/login', methods=['POST'])
def login_post():
    agora = time.time()
    tentativas = session.get('login_attempts', [])
    tentativas = [t for t in tentativas if agora - t < 300]
    if len(tentativas) >= 10:
        flash('Muitas tentativas. Aguarde 5 minutos.', 'danger')
        return redirect(url_for('auth.login'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        tentativas.append(agora)
        session['login_attempts'] = tentativas
        flash('Informe usuário e senha.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.select().where(User.username == username).first()

    if not user or not user.check_password(password):
        tentativas.append(agora)
        session['login_attempts'] = tentativas
        flash('Usuário ou senha inválidos.', 'danger')
        return redirect(url_for('auth.login'))

    if not user.ativo:
        tentativas.append(agora)
        session['login_attempts'] = tentativas
        flash('Usuário desativado. Contate o administrador.', 'danger')
        return redirect(url_for('auth.login'))

    session.pop('login_attempts', None)
    login_user(user)
    session['login_time'] = utcnow().isoformat()
    registrar_log(user, 'login', descricao=f'Usuário {user.username} fez login.')
    return redirect('/')


@auth_route.route('/logout')
def logout():
    if current_user.is_authenticated:
        registrar_log(current_user, 'logout', descricao=f'Usuário {current_user.username} fez logout.')
    logout_user()
    return redirect(url_for('auth.login'))
