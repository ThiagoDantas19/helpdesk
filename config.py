import os
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from database.database import init_db, db
from database.models.usuarios import User
from database.registry import get_all_models
from utils.time import naive_dt
from utils.cache import init_cache
from utils.constants import UPLOAD_DIR
from routes.error_handlers import registrar_erros

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return User.get_or_none(User.id == int(user_id))


def configure_all(app=None, skip_db_init=False):
    if app is None:
        app = Flask(__name__)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    load_dotenv()
    secret = os.environ.get('SECRET_KEY')
    if not secret:
        raise RuntimeError(
            'SECRET_KEY não definida. Crie um arquivo .env baseado em .env.example '
            'ou exporte a variável SECRET_KEY no ambiente.'
        )
    app.config['SECRET_KEY'] = secret
    os.environ['SECRET_KEY'] = secret
    app.config['MAX_CONTENT_LENGTH'] = 55 * 1024 * 1024
    app.config['UPLOAD_DIR'] = UPLOAD_DIR
    app.config['CACHE_TYPE'] = os.environ.get('CACHE_TYPE', 'SimpleCache')
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '60'))
    app.config['CACHE_REDIS_URL'] = os.environ.get('CACHE_REDIS_URL')

    app.template_filter('naive')(naive_dt)

    login_manager.init_app(app)
    CSRFProtect(app)
    init_cache(app)

    if not skip_db_init:
        init_db()
        _criar_tabelas()

    _registrar_rotas(app)
    registrar_erros(app)
    _registrar_comandos(app)
    return app


def _criar_tabelas():
    if db.is_closed():
        db.connect()

    tabelas = get_all_models()
    db.create_tables(tabelas, safe=True)

    from database.migrations import executar_migracoes
    executar_migracoes()


def _registrar_rotas(app):
    from routes.auth import auth_route
    from routes.home import home_route
    from routes.task import task_route
    from routes.user import user_route
    from routes.inventario import inventario_route
    from routes.settings import settings_route
    from routes.setup import setup_route
    from routes.logs import logs_route
    from routes.tarefas import tarefas_route
    from routes.emprestimo import emprestimo_route

    app.register_blueprint(auth_route)
    app.register_blueprint(home_route)
    app.register_blueprint(task_route, url_prefix='/task')
    app.register_blueprint(user_route, url_prefix='/user')
    app.register_blueprint(inventario_route, url_prefix='/inventario')
    app.register_blueprint(settings_route, url_prefix='/settings')
    app.register_blueprint(setup_route)
    app.register_blueprint(logs_route, url_prefix='/logs')
    app.register_blueprint(tarefas_route)
    app.register_blueprint(emprestimo_route, url_prefix='/emprestimo')


def _registrar_comandos(app):
    @app.cli.command('seed')
    def seed_command():
        """Popula o banco com setores, cargos e admin padrão."""
        from database.seed import seed_all
        seed_all()
