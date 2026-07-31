from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from peewee import prefetch
from database.models.chamados import Chamado
from database.models.usuarios import User, Setor
from utils.time import utcnow, hoje_inicio_utc, inicio_mes_utc
from utils.constants import TipoAcesso

home_route = Blueprint('home', __name__)


@home_route.route('/')
@login_required
def home():
    if current_user.tipo_acesso == TipoAcesso.USUARIO.value:
        return redirect(url_for('task.lista_chamados'))

    abertos_hoje = Chamado.select().where(
        Chamado.criado_em >= hoje_inicio_utc(),
        Chamado.status == 'aberto'
    ).count()

    urgentes = Chamado.select().where(
        Chamado.prioridade == 'urgente',
        Chamado.status == 'aberto'
    ).count()

    fechados_mes = Chamado.select().where(
        Chamado.fechado_em >= inicio_mes_utc(),
        Chamado.status == 'fechado'
    ).count()

    aguardando = Chamado.select().where(
        Chamado.status == 'aberto',
        Chamado.operador.is_null(True)
    ).count()

    query = Chamado.select().where(Chamado.status == 'aberto')
    recentes = prefetch(query.order_by(Chamado.criado_em.desc()).limit(7), User, Setor)

    return render_template('index.html',
                           abertos_hoje=abertos_hoje,
                           urgentes=urgentes,
                           fechados_mes=fechados_mes,
                           aguardando=aguardando,
                           recentes=recentes)
