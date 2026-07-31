import logging
from playhouse.migrate import SqliteMigrator
from database.database import db
from utils.time import utcnow
from peewee import DateTimeField, DateField
from database.models.emprestimo import Emprestimo

logger = logging.getLogger(__name__)


def criar_tabela_migracoes():
    db.execute_sql("""
        CREATE TABLE IF NOT EXISTS _migracoes (
            versao TEXT PRIMARY KEY,
            executada_em TEXT NOT NULL
        )
    """)


def migracoes_executadas():
    criar_tabela_migracoes()
    return {row[0] for row in db.execute_sql('SELECT versao FROM _migracoes').fetchall()}


def marcar_executada(nome):
    db.execute_sql(
        "INSERT OR IGNORE INTO _migracoes (versao, executada_em) VALUES (?, ?)",
        (nome, utcnow().isoformat())
    )


def _add_coluna_se_faltar(migrator, tabela, coluna, campo, versao):
    if versao in migracoes_executadas():
        return
    try:
        migrator.add_column(tabela, coluna, campo)
        marcar_executada(versao)
        logger.info('%s OK', versao)
    except Exception as e:
        if 'duplicate column' in str(e).lower():
            marcar_executada(versao)
        else:
            logger.exception('%s ERRO', versao)


def executar_migracoes():
    if db.is_closed():
        db.connect()

    migrator = SqliteMigrator(db)
    executadas = migracoes_executadas()

    if 'v001_default_tipo_acesso' not in executadas:
        try:
            db.execute_sql(
                "UPDATE user SET tipo_acesso = 'usuario' WHERE tipo_acesso = 'funcionario'"
            )
            marcar_executada('v001_default_tipo_acesso')
            logger.info('v001_default_tipo_acesso OK')
        except Exception:
            logger.exception('v001_default_tipo_acesso ERRO')

    _add_coluna_se_faltar(
        migrator, 'patrimonio', 'criado_em', DateTimeField(default=utcnow),
        'v002_criado_em_patrimonio'
    )

    _add_coluna_se_faltar(
        migrator, 'tarefa', 'data_vencimento', DateField(null=True),
        'v003_data_vencimento_tarefa'
    )

    if 'v004_indexes' not in executadas:
        try:
            db.execute_sql(
                "CREATE INDEX IF NOT EXISTS idx_chamadoequipamento_equipamento_id "
                "ON chamadoequipamento(equipamento_id)"
            )
            db.execute_sql(
                "CREATE INDEX IF NOT EXISTS idx_tarefa_usuario_concluida "
                "ON tarefa(usuario_id, concluida)"
            )
            marcar_executada('v004_indexes')
            logger.info('v004_indexes OK')
        except Exception:
            logger.exception('v004_indexes ERRO')

    if 'v005_tipo_vinculo' not in executadas:
        try:
            db.execute_sql("ALTER TABLE user ADD COLUMN tipo_vinculo VARCHAR(255) NOT NULL DEFAULT 'efetivo'")
            marcar_executada('v005_tipo_vinculo')
            logger.info('v005_tipo_vinculo OK')
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                marcar_executada('v005_tipo_vinculo')
            else:
                logger.exception('v005_tipo_vinculo ERRO')

    if 'v006_observacoes' not in executadas:
        try:
            db.execute_sql("ALTER TABLE user ADD COLUMN observacoes TEXT")
            marcar_executada('v006_observacoes')
            logger.info('v006_observacoes OK')
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                marcar_executada('v006_observacoes')
            else:
                logger.exception('v006_observacoes ERRO')

    if 'v007_emprestimo' not in executadas:
        try:
            db.create_tables([Emprestimo])
            marcar_executada('v007_emprestimo')
            logger.info('v007_emprestimo OK')
        except Exception:
            logger.exception('v007_emprestimo ERRO')

    if 'v008_observacoes_devolucao' not in executadas:
        try:
            db.execute_sql("ALTER TABLE emprestimo ADD COLUMN observacoes_devolucao TEXT")
            marcar_executada('v008_observacoes_devolucao')
            logger.info('v008_observacoes_devolucao OK')
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                marcar_executada('v008_observacoes_devolucao')
            else:
                logger.exception('v008_observacoes_devolucao ERRO')

    logger.info('Todas as migracoes concluidas.')
