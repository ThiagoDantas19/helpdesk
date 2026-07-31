from flask import Blueprint, render_template, request
from flask_login import login_required
from routes.auth import admin_required
from database.models.log import LogEntry, User
from math import ceil

logs_route = Blueprint('logs', __name__)

@logs_route.route('/')
@login_required
@admin_required
def ver_logs():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    entidade_filtro = request.args.get('entidade', '').strip()

    query = LogEntry.select().order_by(LogEntry.criado_em.desc())

    if q:
        query = query.where(
            (LogEntry.descricao ** f'%{q}%') |
            (LogEntry.entidade ** f'%{q}%') |
            (LogEntry.acao ** f'%{q}%')
        )

    if entidade_filtro:
        query = query.where(LogEntry.entidade == entidade_filtro)

    total = query.count()
    per_page = 50
    pages = max(1, ceil(total / per_page))
    page = max(1, min(page, pages))

    logs = query.paginate(page, per_page)

    entidades_disponiveis = (
        LogEntry.select(LogEntry.entidade)
        .where(LogEntry.entidade.is_null(False))
        .distinct()
        .order_by(LogEntry.entidade)
    )

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    template = 'logs/_tabela.html' if is_ajax else 'logs/lista.html'
    return render_template(template,
                           logs=logs, page=page, pages=pages, total=total,
                           q=q, entidade_filtro=entidade_filtro,
                           entidades_disponiveis=entidades_disponiveis)
