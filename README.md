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
| `DB_NAME` | Nome do banco. O Compose usa o mesmo valor em `POSTGRES_DB`. |
| `DB_USER` | Usuario do banco. O Compose usa o mesmo valor em `POSTGRES_USER`. |
| `DB_PASSWORD` | Senha do banco. O Compose usa o mesmo valor em `POSTGRES_PASSWORD`. |
| `DB_HOST` | `localhost` quando o banco roda pelo Compose. |
| `DB_PORT` | `5432`, a porta publicada pelo Compose (apenas em `127.0.0.1`). |

Para gerar uma `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

O `docker-compose.yml` le `DB_NAME`, `DB_USER` e `DB_PASSWORD` desse mesmo `.env`,
entao Django e PostgreSQL usam sempre os mesmos valores. `DB_PASSWORD` e obrigatoria:
sem ela o Compose nao sobe. Os valores do `.env.example` (`biblioteca_user` /
`biblioteca_dev`) sao so para desenvolvimento local; troque a senha se quiser.

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

## Desenvolvimento local x implantacao

- **Local:** o PostgreSQL sobe pelo Compose e fica acessivel so na propria maquina
  (`127.0.0.1`). Cada desenvolvedor tem seu banco, com dados proprios.
- **Implantacao (R-015):** os funcionarios devem consultar a mesma base. Para isso o
  Django de producao aponta para um unico PostgreSQL centralizado, definindo `DB_HOST`,
  `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` no ambiente do servidor. Nao e
  preciso mudar codigo, pois `settings.py` le essas variaveis. Esse servidor nao usa o
  Compose de desenvolvimento e deve ter senha propria e acesso restrito pela rede.
  Varios bancos locais independentes nao atendem o requisito.

## Problemas comuns

- `connection refused`: o banco nao esta no ar. Rode `docker compose ps`.
- `password authentication failed`: `DB_USER` ou `DB_PASSWORD` no `.env` diferem do Compose.
  O Postgres so le essas credenciais na primeira criacao do volume; se mudar o Compose
  depois, o volume antigo continua com as credenciais antigas.
- `port is already allocated`: ja existe outro PostgreSQL usando a 5432 na maquina.
- `ImproperlyConfigured: Set the ... environment variable`: falta uma variavel no `.env`.
