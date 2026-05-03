# SoundCircle — Backend

API REST em Flask para o SoundCircle, uma rede social de descoberta e avaliação musical.

**Deploy:** http://100.48.20.219/

---

## Stack

- **Python 3.11+**
- **Flask 3.0.3**
- **Flask-JWT-Extended** (autenticação via cookies HttpOnly)
- **PyMongo 4.7.3** (MongoDB)
- **bcrypt** (hash de senhas)
- **python-dotenv** (variáveis de ambiente)

---

## Pré-requisitos

- Python 3.11 ou superior
- MongoDB rodando localmente (ou string de conexão remota)

> O projeto inclui binários do MongoDB Community em `mongodb/` para uso local sem instalação externa.

---

## Instalação

```bash
# 1. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env  # ou edite .env diretamente
```

---

## Configuração (.env)

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `FLASK_SECRET_KEY` | Secret do Flask | `dev_secret` |
| `JWT_SECRET_KEY` | Secret para tokens JWT | `dev_jwt_secret` |
| `MONGO_DB_STRING` | URI do MongoDB | `mongodb://localhost:27017/soundcircle` |
| `FRONTEND_URL` | URL do frontend (CORS) | `http://localhost:3000` |
| `RAPID_API_SPOTIFY` | Chave da RapidAPI (Spotify) | — |
| `GROQ_API_KEY` | Chave da API Groq (sentimento) | — |

---

## Como rodar

```bash
# Com o ambiente virtual ativado:
python app.py
```

O servidor inicia em `http://127.0.0.1:5000` com `debug=True`.

---

## Estrutura de Diretórios

```
.
├── app.py                 # Entry point Flask
├── config.py              # Configurações e variáveis de ambiente
├── requirements.txt       # Dependências Python
├── .env                   # Variáveis de ambiente (não versionar)
├── models/                # Camada de acesso ao MongoDB
│   ├── user.py
│   ├── comment.py
│   ├── feed.py
│   ├── friend.py
│   ├── promotion.py
│   ├── rating.py
│   └── revoked_token.py
├── routes/                # Blueprints de rotas
│   ├── auth.py
│   ├── feed.py
│   ├── friends.py
│   └── user.py
├── services/              # Integrações externas
│   ├── groq_sentiment.py
│   ├── rapidapi_spotify.py
│   └── seed_tracks.py
├── utils/                 # Utilitários
│   ├── helpers.py
│   └── jwt_helpers.py
└── tests/                 # Testes automatizados (pytest)
    ├── conftest.py
    ├── test_auth.py
    ├── test_feed.py
    ├── test_friends.py
    ├── test_user.py
    └── test_models.py
```

---

## API — Endpoints

### Autenticação (`/api/auth`)

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| `POST` | `/register` | Cadastro (email, senha, display_name) | — |
| `POST` | `/login` | Login (email, senha) | — |
| `POST` | `/logout` | Revoga token e limpa cookie | JWT |
| `GET`  | `/me` | Retorna estado da autenticação | JWT (opcional) |

### Feed (`/api/feed`)

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| `GET`  | `/daily?period=&sort=` | Feed diário/semanal/mensal | JWT |
| `POST` | `/tracks/:id/ratings` | Avaliar música (1.0–5.0) | JWT |
| `DELETE`| `/tracks/:id/ratings` | Remover avaliação | JWT |
| `GET`  | `/tracks/:id/comments` | Listar comentários | JWT |
| `POST` | `/tracks/:id/comments` | Adicionar comentário | JWT |
| `DELETE`| `/tracks/:id/comments/:cid` | Remover comentário | JWT |
| `POST` | `/promote` | Impulsionar música (checkout fake) | JWT |
| `GET`  | `/tracks/:id/sentiment` | Sentimento ajustado da música | JWT |

### Amizades (`/api/friends`)

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| `GET`  | `/` | Lista amigos aceitos | JWT |
| `GET`  | `/pending` | Solicitações pendentes | JWT |
| `POST` | `/` | Enviar solicitação (por display_name) | JWT |
| `PATCH`| `/requests/:id` | Aceitar/recusar solicitação | JWT |
| `DELETE`| `/:friend_id` | Remover amizade | JWT |
| `GET`  | `/:friend_id/ratings` | Avaliações de um amigo | JWT |

### Usuário (`/api/user`)

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| `GET`  | `/profile` | Perfil do usuário logado | JWT |
| `PATCH`| `/profile` | Alterar display_name | JWT |
| `GET`  | `/rated-tracks` | Músicas avaliadas pelo usuário | JWT |

---

## Autenticação

- Tokens JWT são entregues via **cookie HttpOnly** (`access_token_cookie`).
- Expiração: **7 dias**.
- CSRF protection está **desabilitado**.
- Logout insere o `jti` do token em uma blacklist no MongoDB (com índice TTL para limpeza automática).

---

## Testes

```bash
# Rodar todos os testes
pytest -v

# Rodar um arquivo específico
pytest tests/test_auth.py -v
```

Os testes usam um banco de dados separado (`soundcircle_test`) que é limpo automaticamente após cada teste.

---

## Serviços Externos

- **RapidAPI (Spotify)**: busca tracks populares para o feed diário.
- **Groq API**: análise de sentimento dos comentários (modelo `llama-3.3-70b-versatile`).
- **Fallback**: se a RapidAPI falhar, o sistema usa uma lista hardcoded de 20 músicas (`seed_tracks.py`).
