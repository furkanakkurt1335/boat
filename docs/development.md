# Development

## Prerequisites

- Docker & Docker Compose (for web app)
- Node.js 18+ and npm
- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- Rust toolchain via [rustup](https://rustup.rs/) (for desktop app)
- PostgreSQL 16 (if running without Docker)

### Desktop app system libraries (Linux)

```bash
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev \
  librsvg2-dev libjavascriptcoregtk-4.1-dev libsoup-3.0-dev
```

macOS: Xcode Command Line Tools. Windows: Visual Studio C++ Build Tools + WebView2.

## Web App

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and SECRET_KEY

# Development (hot reload on both backend and frontend)
docker compose -f docker-compose.dev.yml up --build

# Backend:  http://localhost:8000 (API docs: http://localhost:8000/docs)
# Frontend: http://localhost:5173
```

### Without Docker

**Backend:**

```bash
cd backend
pip install uv
uv pip install --system -e ".[dev]"

# Start PostgreSQL, then:
export DATABASE_URL="postgresql+asyncpg://boat:boat@localhost:5432/boat"
export SECRET_KEY="your-secret-key"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm ci
npm run dev
# http://localhost:5173, proxies /api → localhost:8000
```

## Desktop App

### Development

```bash
cd frontend
npm ci
npm run tauri:dev
# Opens Tauri window with hot reload
```

### Production build

```bash
cd frontend
npm run tauri:build
# Binary output: frontend/src-tauri/target/release/boat-desktop
```

### Install as CLI

```bash
ln -sf "$(pwd)/frontend/src-tauri/target/release/boat-desktop" ~/.local/bin/boat
```

## Production Deployment

### Via Cloudflare Tunnel

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, SECRET_KEY, DOMAIN

docker compose up -d --build
# Caddy listens on 127.0.0.1:8880 (HTTP only, TLS at Cloudflare edge)

# Add to cloudflared config:
#   - hostname: $DOMAIN
#     service: http://localhost:8880
```

## Common Commands

### Backend

```bash
cd backend

# Run tests
python -m pytest tests/ -v --tb=short

# Lint
ruff check app/
ruff format --check app/

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend

```bash
cd frontend

# Type check
npm run check

# Dev server
npm run dev

# Production build (web)
npm run build
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | Yes (prod) | — | PostgreSQL connection string |
| SECRET_KEY | Yes | — | JWT signing key |
| POSTGRES_PASSWORD | Yes (compose) | — | DB password |
| POSTGRES_USER | No | boat | DB username |
| POSTGRES_DB | No | boat | DB name |
| ACCESS_TOKEN_EXPIRE_MINUTES | No | 480 | JWT token lifetime |
| ALLOWED_ORIGINS | No | `["https://$DOMAIN"]` | CORS origins |
| DOMAIN | No | localhost | For CORS + SvelteKit ORIGIN |
