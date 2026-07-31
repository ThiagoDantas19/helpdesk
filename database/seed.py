import logging
from database.database import db
from database.models.usuarios import Setor, Cargo, User

logger = logging.getLogger(__name__)


def popular_setores_e_cargos():
    if Setor.select().count() == 0:
        logger.info("Alimentando o banco de dados com setores e cargos...")

        esquema_organizacional = {
            'Diretoria': ['Diretor(a)', 'Coordenador(a)'],
            'Financeiro': ['Coordenador(a)', 'Analista', 'Assistente'],
            'Recursos Humanos': ['Coordenador(a)', 'Analista', 'Assistente'],
            'Comercial / Marketing': ['Coordenador(a)', 'Analista', 'Assistente'],
            'Recepção / Triagem': ['Coordenador(a)', 'Recepcionista', 'Auxiliar'],
            'Atendimento Clínico': ['Coordenador(a)','Médico(a) Veterinário(a)', 'Enfermeiro(a) Veterinário(a)'],
            'Internação / UTI': ['Coordenador(a)', 'Médico(a) Veterinário(a)', 'Enfermeiro(a) Veterinário(a)', 'Auxiliar'],
            'Centro Cirúrgico': ['Coordenador(a)', 'Médico(a) Veterinário(a)', 'Enfermeiro(a) Veterinário(a)', 'Auxiliar'],
            'Imagem': ['Coordenador(a)', 'Médico(a) Veterinário(a)', 'Enfermeiro(a) Veterinário(a)', 'Auxiliar'],
            'Laboratório': ['Coordenador(a)', 'Médico(a) Veterinário(a)', 'Auxiliar'],
            'Farmácia Hospitalar': ['Coordenador(a)', 'Farmacêutico(a)', 'Enfermeiro(a) Veterinário(a)', 'Auxiliar'],
            'TI': ['Coordenador(a)', 'Técnico(a) de TI'],
            'Manutenção / Facilities': ['Coordenador(a)', 'Auxiliar']
        }

        with db.atomic():
            for nome_setor, lista_cargos in esquema_organizacional.items():
                setor_db = Setor.create(nome=nome_setor)
                for nome_cargo in lista_cargos:
                    Cargo.create(nome=nome_cargo, setor=setor_db)

        logger.info("Banco de dados populado com sucesso!")


def criar_admin_padrao(nome_completo='Administrador', email='admin@helpdesk.local', username='admin', password=None):
    if not password:
        logger.warning("Senha não fornecida. Admin padrão não criado.")
        return
    if User.select().where(User.username == username).count() == 0:
        setor_ti = Setor.select().where(Setor.nome == 'TI').first()
        cargo_ti = Cargo.select().where(Cargo.nome == 'Técnico(a) de TI').first()
        if not setor_ti or not cargo_ti:
            logger.warning("Setor 'TI' ou cargo 'Técnico(a) de TI' não encontrados. Execute popular_setores_e_cargos() primeiro.")
            return
        admin = User.create(
            nome_completo=nome_completo,
            email=email,
            username=username,
            tipo_acesso='admin',
            tipo_vinculo='efetivo',
            setor=setor_ti,
            cargo=cargo_ti,
            ativo=True
        )
        admin.set_password(password)
        admin.save()
        logger.info(f"Usuário admin padrão criado ({username} / {password})")


def seed_all():
    popular_setores_e_cargos()
    criar_admin_padrao()
