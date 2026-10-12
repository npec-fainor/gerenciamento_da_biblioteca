# Gerenciamento da Biblioteca

Sistema de gerenciamento do acervo de uma biblioteca. Backend em Django com PostgreSQL.

## Pre-requisitos

- Python 3.12 ou superior
- Docker e Docker Compose (para o PostgreSQL)
- Git

## Configuracao do ambiente

Os comandos abaixo partem da raiz do repositorio.

### 1. Ambiente virtual e dependencias

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Se o PowerShell bloquear o script de ativacao, rode
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` e ative de novo.

### 2. Arquivo `.env`

O `.env` fica na raiz do repositorio e nao e versionado. Crie a partir do modelo:

```bash
cp .env.example .env          # Linux / macOS
copy .env.example .env        # Windows (cmd / PowerShell)
```

Preencha os valores:

| Variavel | Descricao |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django. Gere uma propria, nao reaproveite. |
| `DEBUG` | `True` apenas em desenvolvimento. |
| `DB_NAME` | Nome do banco. Deve ser igual a `POSTGRES_DB` do `docker-compose.yml`. |
| `DB_USER` | Usuario do banco. Deve ser igual a `POSTGRES_USER` do `docker-compose.yml`. |
| `DB_PASSWORD` | Senha do banco. Deve ser igual a `POSTGRES_PASSWORD` do `docker-compose.yml`. |
| `DB_HOST` | `localhost` quando o banco roda pelo Compose. |
| `DB_PORT` | `5432`, a porta publicada pelo Compose. |

Para gerar uma `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Atencao: `DB_NAME`, `DB_USER` e `DB_PASSWORD` do `.env` precisam bater com os valores
do servico `db` em `docker-compose.yml`. Confira antes de subir o banco, porque o
`.env.example` nao traz os mesmos valores do Compose por padrao.

### 3. PostgreSQL com Docker Compose

```bash
docker compose up -d db
docker compose ps
```

O servico `db` tem healthcheck. Aguarde o estado `healthy` antes de rodar as migrations.
Os dados ficam no volume `postgres_data`. Para parar o banco sem apagar os dados:

```bash
docker compose stop db
```

Nao use `docker compose down -v` se quiser manter os dados, pois `-v` apaga o volume.

### 4. Migrations

```bash
python backend/manage.py migrate
```

Para conferir se os models e as migrations estao coerentes:

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py showmigrations
```

### 5. Servidor de desenvolvimento

```bash
python backend/manage.py runserver
```

## Testes

Informe sempre os apps explicitamente. A descoberta sem argumentos, a partir da raiz,
nao encontra os testes:

```bash
python backend/manage.py test acervo usuarios --noinput
```

O Django cria um banco temporario `test_<DB_NAME>` no mesmo servidor PostgreSQL e o
remove no final. Os dados do banco de desenvolvimento nao sao alterados, mas o usuario
do banco precisa de permissao para criar bancos (o usuario do Compose tem).

## Problemas comuns

- `connection refused`: o banco nao esta no ar. Rode `docker compose ps`.
- `password authentication failed`: `DB_USER` ou `DB_PASSWORD` no `.env` diferem do Compose.
  O Postgres so le essas credenciais na primeira criacao do volume; se mudar o Compose
  depois, o volume antigo continua com as credenciais antigas.
- `port is already allocated`: ja existe outro PostgreSQL usando a 5432 na maquina.
- `ImproperlyConfigured: Set the ... environment variable`: falta uma variavel no `.env`.
