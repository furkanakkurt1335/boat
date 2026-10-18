# BoAT

Boğaziçi University Annotation Tool — a collaborative tool for linguistic annotation and treebank management using the [Universal Dependencies](https://universaldependencies.org/) framework.

**Project Status:** This repository contains the **2026 rework** of BoAT, transitioning from a Django/Qt stack to a modern FastAPI, SvelteKit, and Tauri architecture. Development is ongoing, and eventually, this "unified" version (supporting both web and desktop) will be migrated to a Boğaziçi organization repository, replacing the legacy [boun-tabi/BoAT](https://github.com/boun-tabi/BoAT).

- **Wiki:** [gitlab.com/furkan5204/boat/-/wikis](https://gitlab.com/furkan5204/boat/-/wikis/home)

## Features

- Sentence-by-sentence annotation (CoNLL-U format)
- Dependency graph visualization
- Multi-user collaboration with inter-annotator agreement
- Treebank management (create, upload, export)
- Advanced search and filtering
- Available as a **web app** and a **desktop app** (Tauri)

## Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL |
| Frontend | SvelteKit 2 + Svelte 5 + TypeScript + Tailwind CSS 4 |
| Desktop | Tauri v2 (Rust) — wraps the same SvelteKit frontend |
| Auth | JWT (python-jose + bcrypt) |
| Server | Uvicorn + Caddy |

## Quick Start (Web App)

The web app requires all three services: PostgreSQL, the FastAPI backend, and the SvelteKit frontend.

### With Docker (recommended)

```bash
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD and SECRET_KEY

# Development (hot reload)
docker compose -f docker-compose.dev.yml up --build

# Backend:  http://localhost:8000 (API docs: /docs)
# Frontend: http://localhost:5173
```

### Without Docker

**Backend:**

```bash
cd backend
pip install uv
uv pip install --system -e ".[dev]"

# Start PostgreSQL, then:
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm ci
npm run dev
# Opens at http://localhost:5173, proxies /api → localhost:8000
```

## Quick Start (Desktop App)

The desktop app wraps the SvelteKit frontend in a Tauri window and works in two modes:

- **Offline** — open `.conllu` files from disk, edit, save (no server needed)
- **Connected** — point at a running BoAT server, login, annotate as if using the web app

### Prerequisites

**Rust toolchain** (rustup.rs):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**System libraries** (Linux/Ubuntu):

```bash
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  libjavascriptcoregtk-4.1-dev \
  libsoup-3.0-dev
```

On macOS, Xcode Command Line Tools are sufficient. On Windows, install the [Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

**Node dependencies:**

```bash
cd frontend
npm ci
```

### Development

```bash
cd frontend
npm run tauri:dev
```

This starts the Vite dev server with `TAURI=1` (using `adapter-static` instead of `adapter-node`) and opens the Tauri window with hot reload.

### Production build

```bash
cd frontend
npm run tauri:build
```

The output binary is in `frontend/src-tauri/target/release/`.

### Usage

When the desktop app opens:

1. **Offline mode** — Click "Open CoNLL-U file" to load a `.conllu` file from disk. Browse sentences, edit annotations in the table, see the dependency graph update live, and save back to disk with `Ctrl+S`.
2. **Connected mode** — Click "Connect to server", enter the URL of a running BoAT instance (e.g. `http://localhost:8000`), login with your credentials. The app then works identically to the web version.

Desktop keyboard shortcuts: `Ctrl+O` (open file), `Ctrl+S` (save), `Ctrl+Shift+S` (save as).

## Directory Structure

```
backend/               # FastAPI backend
  app/
    routers/           # API route handlers
    services/          # CoNLL-U parser, agreement calculator
    models/            # SQLAlchemy models
  alembic/             # Database migrations
  tests/               # pytest test suite

frontend/              # SvelteKit frontend (shared between web and desktop)
  src/
    lib/
      api/             # Typed API client (mode-aware: fetch or Tauri invoke)
      components/      # Svelte components (annotation, graph, layout, desktop)
      stores/          # State management (auth, annotation, mode, theme)
    routes/            # SvelteKit pages
  src-tauri/           # Tauri v2 Rust backend (desktop app)
    src/
      commands.rs      # Tauri command handlers (API dispatch, file I/O)
      conllu.rs        # CoNLL-U parser/exporter (Rust port)
      document.rs      # In-memory document state

docker-compose.yml     # Production deployment
docker-compose.dev.yml # Development with hot reload
Caddyfile              # Reverse proxy config
```

## Publications

- Akkurt, F., Marşan, B., & Üsküdarlı, S. (2022). BoAT v2 — A Web-Based Dependency Annotation Tool with Focus on Agglutinative Languages. In *Proceedings of ALTNLP 2022*. [[arXiv]](https://arxiv.org/abs/2207.01327) [[CEUR-WS]](https://ceur-ws.org/)

## History

- **Original desktop tool:** [boun-tabi/BoAT](https://github.com/boun-tabi/BoAT) (Qt/Python)
- **UniDive Support (2024):** Extended with metadata editing and sentence management during a UniDive STSM at the University of Vienna to support the AMGiC treebank.
- **Current version:** FastAPI + SvelteKit rewrite with Tauri desktop app (2026 unified version).
