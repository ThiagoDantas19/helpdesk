# Manual de Uso — HelpDesk IT

Sistema de gestão de ativos de TI, auditorias de equipamentos e chamados de suporte.
Este manual cobre instalação, configuração e o dia a dia de cada módulo.

---

## 1. Requisitos

- Python 3.12+ (desenvolvido/testado com 3.14)
- Acesso à internet apenas na primeira instalação (pip e CDNs)

## 2. Instalação (primeira vez)

```bash
cd crud
python -m venv venv
source venv/bin/activate            # Linux/macOS
venv\Scripts\activate               # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt # opcional (testes)

cp .env.example .env                # edite o SECRET_KEY (qualquer valor longo e aleatório)
```

### Criando os dados iniciais

Duas opções (qualquer uma cria setores, cargos e o admin):

**Via interface** (recomendado):
1. `python main.py` e acesse `http://localhost:5000`
2. Siga a página de configuração (setup) — preencha admin, setor/cargo e senha

**Via linha de comando**:
```bash
flask --app main seed               # cria setores, cargos e admin padrão (admin/admin)
```

## 3. Iniciar o servidor

```bash
python main.py                      # http://localhost:5000
```

- O banco (`customermanagement.db`) e as migrações são criados/corrigidos
  automaticamente na inicialização.
- Para desenvolvimento com debug: `FLASK_DEBUG=1 python main.py`
- Em produção use um servidor WSGI (seção 10).

## 4. Perfis de acesso

| Perfil | O que pode fazer |
|---|---|
| **Usuário** | Dashboard; criar e acompanhar os próprios chamados |
| **Técnico** | Tudo do usuário + todos os chamados + inventário (cadastrar, editar, auditar, exportar) + empréstimos |
| **Admin** | Tudo do técnico + usuários, setores, cargos, credenciais, logs e exclusões |

## 5. Dashboard (`/`)

- Visão geral: quantidade de chamados (por status/prioridade), equipamentos ativos,
  tarefas do dia.
- Atalhos para os módulos principais.

## 6. Chamados (HelpDesk)

1. **Abrir chamado**: menu "Chamados" → "Abrir Chamado" — título, descrição,
   categoria/prioridade. O usuário comum só vê os próprios.
2. **Lista**: filtros por status, prioridade e busca; atualização AJAX.
3. **Assumir**: técnico assume o chamado (responsável).
4. **Responder**: adiciona respostas ao histórico.
5. **Anexos**: adicionar/remover arquivos.
6. **Editar/excluir**: admin/técnico conforme permissão.
7. **Exportar CSV**: botão na lista — baixa todos os chamados filtrados.

## 7. Inventário

Cobre 5 tipos: **Computador, Celular, Telefone IP (ramal), Impressora, Item diverso**
+ **Linhas telefônicas** (números com ramais vinculados a celulares).

### Cadastrar equipamento
1. Menu "Inventário" → escolha o tipo → "Novo"
2. Preencha: código de etiqueta (patrimônio), nome, setor, responsável, modelo e
   demais campos específicos do tipo
3. Ativo/Inativo controla a disponibilidade para empréstimos

### Detalhes e edição
- Tela de detalhes mostra fotos/anexos e o histórico de auditorias
- "Editar" altera os dados do patrimônio

### Excluir (apenas admin)
- Remove o patrimônio **e tudo vinculado** (chamados vinculados, auditorias,
  anexos, empréstimos) e **apaga os arquivos do disco** — confirme antes.

## 8. Auditorias

Processo periódico de conferência física dos equipamentos.

1. Em "Inventário" → equipamento → **"Auditar"**
2. Marque os itens do checklist (apps, fotos, WhatsApp, avarias etc. — varia por tipo)
   e adicione observações
3. Salve — o status geral (OK/Falha) é calculado automaticamente
4. **Histórico**: "Auditorias" no equipamento mostra todas as conferências e anexos
5. **Editar auditoria**: corrige um checklist já lançado
6. **Exportar**: CSV do histórico do equipamento
7. **Relatório mensal de celulares** (técnico/admin): menu de celulares →
   "Exportar mensal" — lista as auditorias do mês corrente de todos os celulares

> Dica: realize a auditoria no ritmo definido pela sua equipe (semanal/mensal) e
> mantenha os anexos (fotos de avarias) para rastreabilidade.

## 9. Empréstimos

Controla equipamento emprestado a funcionários.

1. "Empréstimos" → "Novo": escolha o patrimônio **ativo**, funcionário, datas e observações
2. Lista mostra empréstimos em aberto/encerrados
3. **Devolver**: registra a devolução (com observações opcionais)
4. Excluir: remove o registro (admin)

## 10. Tarefas pessoais

- Lista de tarefas (AJAX): criar, concluir (toggle), excluir
- **Calendário**: tarefas com data de vencimento visualizadas por dia

## 11. Credenciais (cofre de senhas) — admin

- Guarda senhas de serviços/sistemas com **criptografia** (Fernet)
- **"Revelar"** mostra a senha (ação registrada no log)
- Nunca guarde credenciais em arquivos de texto soltos

## 12. Usuários, Setores e Cargos — admin

- **Usuários**: criar/editar com perfil (usuário/técnico/admin), setor, cargo,
  vínculo e observações; inativar sem excluir
- **Setores/Cargos**: organização hierárquica (setor → cargos)
- Alterar cargo atualiza o vínculo do usuário (busca AJAX de cargos do setor)

## 13. Logs do sistema — admin

- Registro de todas as ações: login, CRUD, auditorias, revelação de senha
- Filtros: busca textual e por entidade; paginação (50 por página)
- Use o log para auditoria e solução de problemas

## 14. Backup (importante)

Faça backup do **banco** e dos **uploads**:

```bash
# Banco (recomendado: backup consistente mesmo com o app aberto)
sqlite3 customermanagement.db ".backup 'backup_$(date +%F).db'"

# Arquivos
cp -r uploads/ "backup_$(date +%F)/"
```

Restaurar: pare o app, substitua o arquivo `.db` e a pasta `uploads/` e inicie de novo.

## 15. Produção

```bash
pip install gunicorn
gunicorn -w 1 -b 0.0.0.0:8000 main:app
```

- `SECRET_KEY` forte no `.env` do servidor
- Proxy reverso com HTTPS (nginx/caddy)
- `debug` fora do ar (não use `FLASK_DEBUG`)
- 1 worker com SQLite; se precisar de vários workers, configure Redis
  (`CACHE_TYPE=RedisCache` + `CACHE_REDIS_URL` no `.env`) e avalie PostgreSQL
- Agende o backup da seção 14 (cron)

## 16. Solução de problemas

| Problema | Solução |
|---|---|
| "SECRET_KEY não definida" | Crie/edite o `.env` (veja `.env.example`) |
| Esqueceu a senha do admin | No shell: `flask --app main seed` recria o admin padrão se não existir; ou edite via `python` resetando com `User.set_password` |
| "database is locked" | Há 1 processo usando o banco — feche outros `python main.py` e rode com 1 worker |
| Upload negado | Verifique extensão, tamanho (máx. 55 MB) e conteúdo (magic bytes) |
| Página 500 | Veja os logs do terminal; use `FLASK_DEBUG=1` para detalhes em desenvolvimento |
| Relatório mensal vazio | Nenhuma auditoria de celular no mês corrente |

## 17. Testes

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q     # 143 testes
```
