# HelpDesk IT — Gestão de Ativos / Inventory Management

Sistema web interno de helpdesk e gestão de patrimônio de TI, com auditorias periódicas de equipamentos, abertura de chamados e controle de empréstimos.

Internal IT helpdesk and asset management web app with periodic equipment audits, service tickets and loan control.

---

## Português (PT-BR)

### Funcionalidades
- **Autenticação com perfis** — login com controle de acesso: `admin`, `tecnico` e `usuario` (proteção CSRF em todos os formulários).
- **Inventário de patrimônio** — cadastro e edição de celulares, computadores, impressoras, telefones IP e itens diversos, com fotos/arquivos anexados.
- **Auditorias periódicas** — checklist por tipo de equipamento (apps, fotos, whatsapp, avarias, etc.), histórico por patrimônio e **exportação CSV** (completa e relatório mensal).
- **Chamados / tickets** — abertura e acompanhamento com vínculo de equipamentos.
- **Empréstimos** — registro de empréstimo/devolução de equipamentos entre funcionários.
- **Logs de auditoria** — trilha de ações (criar, editar, deletar) registrada por usuário.
- **Migrações versionadas** — banco evolui de forma incremental na inicialização.
- **143 testes automatizados** (pytest) cobrindo rotas, permissões e serviços.

### Tecnologias
- **Backend:** Python 3.14, Flask 3.1, Flask-Login, Flask-WTF (CSRF), Flask-Caching
- **ORM:** Peewee 4.0 (SQLite com WAL)
- **Frontend:** Jinja2, HTML/CSS vanilla (sem frameworks)
- **Testes:** pytest

### Como rodar
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# crie o .env a partir do exemplo
cp .env.example .env
# edite o SECRET_KEY

# opcional: dados iniciais (setores, cargos, admin padrão)
flask seed

python main.py
```
Acesse `http://localhost:5000`.

### Testes
```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

### Estrutura
```
config.py            Configuração da aplicação
main.py              Entrypoint
database/            Modelos Peewee, migrações versionadas, seed
routes/              Blueprints (auth, task, user, inventario, ...)
services/            Camada de serviço (ex.: EquipamentoService)
templates/           Jinja2
tests/               Suite de testes (pytest)
utils/               Cache, uploads, constantes, helpers
```

### Segurança
- `SECRET_KEY` obrigatória via `.env` (exigida na inicialização).
- CSRF habilitado globalmente.
- Limite de upload de arquivos (55 MB) com validação de extensão.
- Senhas protegidas (hash) e permissões verificadas por decorator de rota.

### Notas de produção
O projeto usa SQLite com WAL — adequado para uso interno com um único processo. Para múltiplos workers/processos: use `CACHE_TYPE=RedisCache` + `CACHE_REDIS_URL` no `.env` e considere migrar para PostgreSQL (o Peewee abstrai a troca).

---

## English

### Features
- **Role-based authentication** — `admin`, `technician` and `user` profiles with CSRF-protected forms.
- **Asset inventory** — register/edit phones, computers, printers, VoIP phones and miscellaneous items with attached files.
- **Periodic audits** — per-device checklists (apps, photos, whatsapp, damages...), per-asset history and **CSV export** (full + monthly report).
- **Service tickets** — create and track tickets linked to assets.
- **Equipment loans** — track loans/returns between employees.
- **Audit logs** — full action trail (create, edit, delete) per user.
- **Versioned migrations** — incremental DB schema updates on startup.
- **143 automated tests** (pytest) covering routes, permissions and services.

### Tech stack
- **Backend:** Python 3.14, Flask 3.1, Flask-Login, Flask-WTF (CSRF), Flask-Caching
- **ORM:** Peewee 4.0 (SQLite with WAL)
- **Frontend:** Jinja2, vanilla HTML/CSS
- **Tests:** pytest

### Run locally
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit SECRET_KEY

flask seed             # optional: initial data (sectors, roles, default admin)
python main.py
```
Open `http://localhost:5000`.

### Tests
```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

### Security
- `SECRET_KEY` required via `.env` (app refuses to start without it).
- Global CSRF protection.
- 55 MB upload limit with extension validation.
- Hashed passwords and route-level permission decorators.

### Production notes
Built on SQLite with WAL — great for single-process internal use. For multiple workers: set `CACHE_TYPE=RedisCache` + `CACHE_REDIS_URL` in `.env` and consider PostgreSQL (Peewee makes the switch straightforward).
