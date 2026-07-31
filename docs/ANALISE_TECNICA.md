# Análise Técnica Completa — HelpDesk IT

> Documento de arquitetura, segurança e histórico do projeto.
> Versão: 2026-07-31 (pós-melhorias) · Suíte de testes: **143 passando**

---

## 1. Visão Geral

| Item | Valor |
|---|---|
| Diretório raiz | `crud/` (repositório `ThiagoDantas19/helpdesk`) |
| Framework | Flask 3.1.3 (Python 3.14) |
| ORM | Peewee 4.0.5 (`playhouse.migrate` para migrações) |
| Banco de dados | SQLite `customermanagement.db` (WAL mode, FK ativo) |
| Autenticação | Flask-Login (sessão via cookie assinado) |
| CSRF | Flask-WTF `CSRFProtect` global + meta tag + injeção automática no JS |
| Cache | Flask-Caching (`SimpleCache` por padrão; `RedisCache` configurável) |
| Frontend | Bootstrap 5.3, CSS/JS customizados (`style.css`, `cru.js`) |
| Testes | pytest 9.1.1 — 143 testes em 10 arquivos + conftest |
| Uploads | Pasta `uploads/`, limite de 55 MB, validação por magic bytes |

---

## 2. Mapa de Diretórios

```
crud/
├── main.py                          # Entrypoint (debug controlado por FLASK_DEBUG)
├── config.py                        # Factory configure_all(): app, BD, cache, blueprints
├── requirements.txt                 # Dependências de produção
├── requirements-dev.txt             # Dependências de desenvolvimento (pytest)
├── .env.example                     # Modelo de variáveis (SECRET_KEY, cache)
├── .gitignore                       # .env, *.db, uploads/, venvs fora do git
├── README.md                        # Apresentação bilingue (PT/EN)
│
├── database/
│   ├── database.py                  # db = Proxy() + init_db() (desacopla inicialização)
│   ├── migrations.py                # 8 migrações versionadas (v001 → v008, em ordem)
│   ├── registry.py                  # Registro central de modelos para create_tables
│   ├── seed.py                      # Setores/cargos (estrutura genérica mínima) + admin padrão
│   ├── seed_personalizado.py        # (LOCAL, fora do git) estrutura real da unidade — sobrescreve o seed genérico
│   └── models/
│       ├── usuarios.py              # Setor, Cargo, User (hash de senha, FK setor/cargo)
│       ├── equipamentos.py          # 15 modelos: Patrimonio + específicos + auditorias
│       ├── chamados.py              # Chamado, ChamadoEquipamento, ChamadoAnexo
│       ├── log.py                   # LogEntry + registrar_log()
│       ├── tarefa.py                # Tarefa (to-do pessoal)
│       ├── emprestimo.py            # Emprestimo (FK patrimônio, CASCADE)
│       └── credencial.py            # Credencial (senhas criptografadas)
│
├── routes/
│   ├── auth.py                      # Login/logout + decorators admin_required/tecnico_required
│   ├── home.py                      # Dashboard
│   ├── user.py                      # CRUD de usuários + buscar-cargos AJAX
│   ├── task.py                      # Chamados (CRUD, anexos, assumir, responder, export CSV)
│   ├── tarefas.py                   # API REST de tarefas pessoais
│   ├── settings.py                  # CRUD setores, cargos, credenciais (cofre)
│   ├── setup.py                     # Setup first-run (seed via UI)
│   ├── logs.py                      # Logs de auditoria (paginado, filtros, AJAX)
│   ├── emprestimo.py                # Empréstimos (novo, devolver, deletar)
│   └── inventario/
│       ├── __init__.py              # Blueprint + upload/anexo genéricos
│       ├── computador.py / celular.py / telefone.py / impressora.py / item.py
│       │                           # Wrappers de ~40 linhas sobre EquipamentoService
│       └── linha.py                 # Linhas telefônicas (CRUD direto)
│
├── services/
│   ├── __init__.py
│   └── equipamento_service.py       # Template Method: CRUD + auditoria + export genéricos
│
├── utils/
│   ├── __init__.py
│   ├── constants.py                 # Enums: TipoEquipamento, StatusChamado, Prioridade, TipoAcesso
│   ├── time.py                      # utcnow(), naive_dt(), hoje_inicio_utc()
│   ├── crypto.py                    # encrypt()/decrypt() via Fernet (chave derivada da SECRET_KEY)
│   ├── compartilhado.py             # validar_arquivo(), salvar_midia(), export CSV de auditorias
│   └── cache.py                     # Flask-Caching: cache + init_cache(app)
│
├── templates/
│   ├── base.html                    # Layout base (navbar, tema dark/light, CSRF, sessão)
│   ├── login.html, setup.html, index.html, 403/404/500.html
│   ├── usuario/ (4)  chamado/ (7)  emprestimo/ (3)  logs/ (2)  settings/ (7)
│   └── inventario/
│       ├── hub.html, form_auditoria_edit.html
│       └── celular|computador|impressora|item|telefone/ (6 cada) + linha/ (4)
│
├── static/  → style.css, cru.js (AJAX CRUD + toasts + timer de sessão)
├── uploads/ → mídia de auditorias e itens (.gitkeep versionado)
├── docs/
│   ├── ANALISE_TECNICA.md           # Este documento
│   └── MANUAL_DE_USO.md             # Manual do usuário final
└── tests/
    ├── conftest.py                  # BD :memory:, seed, helpers (login, csrf, criar_tecnico...)
    ├── test_validations.py          # Login/logout/validações de acesso
    ├── test_authorization.py        # Permissões por perfil
    ├── test_inventario_crud.py      # CRUD + auditoria dos 5 equipamentos
    ├── test_auditoria_export.py     # Export CSV de auditorias
    ├── test_emprestimo.py           # Fluxo de empréstimos
    ├── test_limpeza_delete.py       # Delete com vínculos/arquivos + relatório mensal
    ├── test_settings_crud.py        # Setores, cargos, credenciais
    ├── test_tarefas_api.py          # API de tarefas
    └── test_upload_validacao.py     # Magic bytes, extensões, limites
```

---

## 3. Banco de Dados — 25 Tabelas

**Usuários e organização:** `setor`, `cargo`, `user`

**Inventário (Patrimonio + especializações):** `patrimonio` (tabela-base: código de etiqueta,
nome, tipo, setor, responsável, ativo), `computador`, `celular`, `numerotelefone`, `telefoneip`,
`impressora`, `itemdiverso`

**Auditoria:** `auditoria` (status geral, setor no momento, técnico, observações) +
`auditoriacelular`, `auditoriacomputador`, `auditoriatelefone`, `auditoriaimpressora`,
`auditoriaitemdiverso` (checklists por tipo, `unique` na FK de auditoria) +
`auditoriaanexo`, `itemanexo` (mídia em disco)

**Operacional:** `chamado`, `chamadoequipamento` (vínculo N:N com índice em `equipamento_id`),
`chamadoanexo`, `emprestimo` (com `observacoes_devolucao`), `tarefa`, `credencial`, `logentry`

### Migrações (8, executadas em ordem na inicialização)

| Versão | Ação |
|---|---|
| v001 | Normaliza `tipo_acesso` ('funcionario' → 'usuario') |
| v002 | `patrimonio.criado_em` (DateTime) |
| v003 | `tarefa.data_vencimento` (Date, nullable) |
| v004 | Índices: `chamadoequipamento(equipamento_id)`, `tarefa(usuario_id, concluida)` |
| v005 | `user.tipo_vinculo` (VARCHAR, default 'efetivo') |
| v006 | `user.observacoes` (TEXT) |
| v007 | Cria tabela `emprestimo` |
| v008 | `emprestimo.observacoes_devolucao` (TEXT) |

O controle é feito pela tabela `_migracoes` (versão + timestamp). As operações são
idempotentes (tratam "duplicate column") — seguras para rodar a cada startup.

---

## 4. Relações Entre Tabelas (Diagrama Lógico)

```
SETOR 1───* CARGO
SETOR 1───* USER *───1 CARGO
USER 1───* CHAMADO
CHAMADO 1───* CHAMADOEQUIPAMENTO *───1 PATRIMONIO (vínculo N:N, indexado)
CHAMADO 1───* CHAMADOANEXO
CHAMADO 1───* TAREFA (pessoal: user_id)

PATRIMONIO 1───1 COMPUTADOR / CELULAR / TELEFONEIP / IMPRESSORA / ITEMDIVERSO
PATRIMONIO 1───* NUMEROTELEFONE *───1 CELULAR (ramais)
PATRIMONIO 1───* AUDITORIA *───1 AUDITORIA{COMPUTADOR,CELULAR,TELEFONE,IMPRESSORA,ITEMDIVERSO}
AUDITORIA 1───* AUDITORIAANEXO
PATRIMONIO 1───* ITEMANEXO
PATRIMONIO 1───* EMPRESTIMO (CASCADE; devolução registra observações)

USER 1───* LOGENTRY
USER 1───* CREDENCIAL (senhas criptografadas — cofre)
```

Regras de integridade importantes:
- FKs de `auditoria*.auditoria` e `emprestimo.patrimonio` usam `on_delete='CASCADE'`;
  `patrimonio.setor/responsavel` usam `SET NULL`.
- `service.deletar()` remove em ordem: vínculos de chamados → detalhes de auditoria →
  anexos → patrimônio, e **apaga os arquivos do disco** correspondentes.
- Excluir patrimônio deixa os arquivos de `uploads/` órfãos se interrompido no meio
  (o delete roda dentro de `db.atomic()`; arquivos são removidos só após o commit).

---

## 5. Sistema de Permissões

| Perfil | Acesso |
|---|---|
| `usuario` | Próprios chamados (ver/criar) e dashboard |
| `tecnico` | Todos os chamados + inventário completo (ver/auditar/exportar) + empréstimos |
| `admin` | Tudo acima + CRUD de usuários, setores, cargos, credenciais, logs, deletar |

Implementação (`routes/auth.py`):
- `@admin_required` → perfil != ADMIN → 403
- `@tecnico_required` → perfil fora de (ADMIN, TECNICO) → 403
- `pode_ver_chamado()` → admin/técnico veem qualquer; usuário só o seu

---

## 6. Rotas Principais (Endpoints)

**Autenticação** — `auth_route`
- `GET/POST /login` · `GET /logout`

**Dashboard** — `home_route`: `GET /`

**Usuários** — `user_route`
- `GET/POST /user/` · `GET /user/new` · `GET /user/<id>` · `GET/POST /user/<id>/edit`
- `DELETE /user/<id>/delete` · `GET /user/buscar-cargos` (AJAX)

**Chamados** — `task_route`
- `GET/POST /task/` · `GET /task/new` · `GET /task/<os_id>` · `GET/POST /task/<os_id>/edit`
- `POST /task/<os_id>/assumir` · `POST /task/<os_id>/responder` · `DELETE /task/<os_id>/delete`
- `POST /task/<os_id>/anexar` · `DELETE /task/<os_id>/anexo/<anexo_id>/delete`
- `GET /task/exportar` (CSV) · `GET /task/uploads/<filename>`

**Tarefas (API)** — `tarefas_route`
- `GET/POST /api/tarefas` · `POST /api/tarefas/<id>/toggle` · `DELETE /api/tarefas/<id>`
- `GET /api/tarefas/calendario`

**Configurações** — `settings_route`
- `GET /settings/` (hub) · CRUD `/settings/setor*`, `/settings/cargo*`, `/settings/credencial*`
- `POST /settings/credencial/<id>/reveal` (revelar senha)

**Setup** — `setup_route`: `GET /setup/` · `POST /setup/seed`

**Logs** — `logs_route`: `GET /logs/` (paginado, filtro q/entidade, AJAX)

**Empréstimos** — `emprestimo_route`
- `GET/POST /emprestimo/` · `GET /emprestimo/new` · `GET /emprestimo/<id>`
- `POST /emprestimo/<id>/devolver` · `POST /emprestimo/<id>/delete`

**Inventário** — `inventario_route` (padrão repetido para computador/celular/telefone/
impressora/item)
- `GET/POST /inventario/<tipo>/` (lista/criar) · `GET /inventario/<tipo>/new`
- `GET /inventario/<tipo>/<patr_id>` (detalhes) · `GET/POST .../edit|update`
- `DELETE .../delete` · `GET/POST .../auditar` · `GET .../auditorias` (histórico)
- `GET .../auditorias/export` (CSV) · `GET /inventario/celular/export/mensal` (relatório)
- `POST /inventario/auditoria/<audit_id>/anexar` · `GET /inventario/auditoria/<id>/edit`
- `POST /inventario/auditoria/<id>/update` · `DELETE /inventario/auditoria/anexo/<id>/delete`
- `POST /inventario/item/<patr_id>/foto` · `DELETE /inventario/foto-item/<anexo_id>/delete`
- `GET /inventario/` (hub) · Linhas: CRUD `/inventario/linha*`

---

## 7. Funcionalidades

- Chamados (tickets) com status, prioridade, responsável, anexos e CSV
- Inventário de 5 tipos de equipamento + linhas telefônicas (ramais)
- Auditorias periódicas com checklist por tipo, histórico e exportação CSV
  (completa por patrimônio e relatório mensal de celulares)
- Empréstimos de equipamentos com devolução registrada
- Cofre de credenciais (senhas criptografadas com Fernet)
- Tarefas pessoais com calendário
- Log de auditoria completo (quem fez o quê, quando, IP)
- CRUD de usuários, setores e cargos
- **Setup first-run e seed via interface**: `seed.py` aplica uma estrutura genérica
  mínima (setor TI + cargos) no repositório público; se o arquivo local
  `database/seed_personalizado.py` existir (fora do git), ele é usado no lugar —
  mantendo a estrutura organizacional real fora do repositório.
- Tema dark/light, dashboard com indicadores

---

## 8. Arquitetura

- **Proxy Pattern**: `database/database.py` expõe `db = Proxy()`; testes inicializam
  com `SqliteDatabase(':memory:')` sem tocar nos modelos.
- **Service Layer**: `EquipamentoService` (Template Method) concentra CRUD + auditoria +
  export dos 5 tipos; as rotas são wrappers de configuração (~40 linhas cada). O `deletar()`
  genérico remove vínculos e arquivos.
- **Config Factory**: `configure_all(skip_db_init=bool)` separa app de banco; comandos
  CLI (`flask seed`).
- **Timezone**: `utcnow()` em `utils/time.py` em todos os modelos/rotas; `naive_dt` para
  exibição.
- **Enums**: `TipoEquipamento`, `StatusChamado`, `PrioridadeChamado`, `TipoAcesso` —
  sem magic strings.
- **Cache**: `utils/cache.py` envolve Flask-Caching. `get_form_context()` guarda **dicts**
  (serializáveis) em vez de modelos; suporta `RedisCache` via env sem mudar código cliente.
- **Migrations**: versionadas e idempotentes, executadas no startup (`_criar_tabelas()`).

### Melhorias recentes (2026-07-31)
1. **Import circular eliminado**: `UPLOAD_DIR` movido para `utils/constants.py`;
   `config.py` e `utils/compartilhado.py` importam de lá.
2. **Código morto removido**: checagem inalcançável de `tipo_acesso == 'usuario'`
   no export CSV de chamados (rota é `@tecnico_required`).
3. **Migrações em ordem sequencial** v001→v008 + `v004_indexes`; excessões com `e`
   não utilizado limpas (helper `_add_coluna_se_faltar`).
4. **N+1 eliminado em CSVs**: detalhes de auditoria pré-carregados via `prefetch`
   (fk backref); `export_auditoria_csv` recebe lista `(auditoria, detalhes)`.
5. **ChamadoEquipamento polimórfico**: delete explícito de vínculos no `deletar()`;
   FKs de detalhes de auditoria agora `CASCADE` (modelos + delete explícito para
   bases existentes); `_resolve_equipamentos` trata erros.
6. **Setup sem I/O em toda requisição**: `before_app_request` só roda em GET, ignora
   `/setup/`, `/static/`, `/api/` e AJAX.
7. **Órfãos eliminados**: foto de 3,6 MB sem registro no DB removida do `uploads/`.
8. **Cache compartilhável**: trocado para Flask-Caching (Redis via env).
9. **Dependências separadas**: `requirements-dev.txt` (pytest) desacoplado de produção.
10. **N+1 em empréstimos**: lista de patrimônios usa UNION (`|`) em vez de 5 consultas.
11. **Relatório mensal corrigido**: filtro por intervalo de datas (o uso de
    `data_auditoria.month` gerava UDF incompatível com SQLite); detalhes carregados
    em lote (3 mapas) — sem N+1.
12. **Exclusão com FK segura**: detalhes de auditoria deletados antes do patrimônio;
    testes cobrem vínculos + arquivos + 404.

---

## 9. Tecnologias

Python 3.14 · Flask 3.1.3 · Flask-Login 0.6.3 · Flask-WTF 1.2.2 · Flask-Caching 2.4.1 ·
Peewee 4.0.5 (playhouse.migrate) · Werkzeug 3.1.8 · cryptography 44.0.0 ·
python-dotenv 1.1.0 · SQLite (WAL) · Bootstrap 5.3.3 · pytest 9.1.1

---

## 10. Changelog

### Sessão 1 e 2 — Bugs, Segurança, CSRF/XSS/Criptografia (originais)
- Correções críticas de segurança e bugs da versão inicial (ver histórico).

### Sessão 3 — Refatoração (2024-07-30)
- `db` global virou `Proxy()`; config sem imports circulares; `configure_all()`
  quebrada em métodos privados; `EquipamentoService` criado (~70% menos duplicação
  nas 6 rotas de inventário); `except Exception` genéricos removidos; timezone
  padronizada via `utils/time.py`; Enums em `utils/constants.py`; bug JS (const
  duplicada) corrigido; cache com interface pronta para Redis. **132 testes passando.**

### Sessão 4 — Qualidade e Arquitetura (2026-07-31)
- Os 12 itens listados na seção 8 ("Melhorias recentes"). **143 testes passando.**
- `main.py`: debug agora controlado por `FLASK_DEBUG` (env), não hardcoded.
- Documentação técnica e manual de uso adicionados em `docs/`.

---

## 11. Checklist de Segurança (novas páginas)

- [x] **Autenticação**: `@login_required` em toda rota protegida; redirect p/ `/login`.
- [x] **Autorização**: `@admin_required`/`@tecnico_required`; permissão por objeto
      (`pode_ver_chamado`); nunca confiar em esconder links.
- [x] **CSRF**: proteção global; forms com `{{ csrf_token() }}`; AJAX com header
      `X-CSRFToken` (cru.js).
- [x] **XSS**: Jinja2 autoescape; `|safe` apenas em conteúdo do servidor.
- [x] **Input**: `request.args.get(type=int)`; senha ≥ 4; upload com magic bytes +
      extensão + limite 55 MB; path traversal bloqueado (404).
- [x] **Criptografia**: senhas com hash (Werkzeug); segredos com Fernet;
      SECRET_KEY só via `.env`.
- [x] **Database**: `db.atomic()` em multi-tabelas; Enums; `utcnow()`; ORM parametriza.
- [x] **Logs**: `registrar_log()` com usuário/ação/entidade/IP.
- [x] **Erros**: flash para erros esperados; `logger.exception` para inesperados;
      sem stack trace ao usuário.
- [x] **Frontend**: CSRF injetado; tema dark/light; CDNs com SRI.
- [x] **Produção**: `debug` via env; WSGI (gunicorn/waitress); HTTPS; backup do `.db`
      e `uploads/`; SQLite recomendado com 1 worker (Postgres + Redis p/ multi-worker).

---

## 12. Executando Testes

```bash
python -m pytest tests/ -q        # 143 testes (~1 min)
python -m pytest tests/test_limpeza_delete.py -q   # subset
```
