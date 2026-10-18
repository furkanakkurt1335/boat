# Current Status

Last updated: 2026-03-02

## Architecture

```
backend/                   # FastAPI backend
  app/
    core/                  # Config, database, JWT security
    models/                # SQLAlchemy 2.0 mapped classes (8 tables)
    schemas/               # Pydantic request/response models
    routers/               # API route handlers (9 routers)
    services/              # CoNLL-U parser, agreement calculator
  alembic/                 # Database migrations
  tests/                   # pytest + pytest-asyncio test suite

frontend/                  # SvelteKit frontend (shared web + desktop)
  src/
    lib/
      api/                 # Typed fetch client (mode-aware: fetch or Tauri invoke)
      components/
        annotation/        # Table, cell, toolbar, searchable select, FEATS/MISC editor
        graph/             # DisplacyGraph (SVG arcs), DiffView
        common/            # Button, Input, Modal, Toast, Tooltip, Skeleton
        layout/            # Navbar, Breadcrumb
        desktop/           # ConnectDialog, DesktopShortcuts
      stores/              # auth, annotation, mode, preferences, theme, toast
      utils/               # Keyboard shortcuts, UD tagsets, cn()
    routes/                # SvelteKit pages
  src-tauri/               # Tauri v2 Rust backend (desktop app)
    src/
      commands.rs          # API dispatch + file I/O commands
      conllu.rs            # CoNLL-U parser/exporter (Rust)
      document.rs          # In-memory document state

docker-compose.yml         # Production deployment
docker-compose.dev.yml     # Development with hot reload
Caddyfile                  # Reverse proxy (Caddy)
```

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI | 0.115 |
| ORM | SQLAlchemy | 2.0 (async, asyncpg) |
| Database | PostgreSQL | 16 |
| Migrations | Alembic | async |
| Frontend | SvelteKit | 2 |
| UI Framework | Svelte | 5 (runes) |
| Styling | Tailwind CSS | 4 |
| Desktop | Tauri | 2 (Rust) |
| Auth | JWT | python-jose + bcrypt |
| Server | Uvicorn + Caddy | |
| CI/CD | GitLab CI | |
| Linting | ruff (backend), svelte-check (frontend) | |
| Tests | pytest + pytest-asyncio | |
| Packaging | uv (backend), npm (frontend) | |

## Features

### Annotation
- Sentence-by-sentence editing of all 10 CoNLL-U fields
- Inline validation (UPOS tags, HEAD references, self-loops)
- Searchable dropdowns for UPOS and DEPREL (full UD tagset)
- FEATS editor with predefined UD morphological features
- MISC editor with free-form key=value pairs
- Multiword token support (e.g., ID `1-2`)
- Add/remove rows

### Visualization
- Interactive dependency graph (displaCy-style SVG arcs)
- Diff view comparing two annotations
- Live graph updates on cell edits

### Collaboration
- Multi-user annotation with JWT authentication
- Annotation status tracking (New / Draft / Complete)
- Inter-annotator agreement computation
- Per-sentence comment threads
- Treebank-level annotation guidelines

### Management
- Treebank CRUD (create, upload CoNLL-U, export, delete)
- Progress tracking (% annotated per treebank)
- Advanced search (filter by any CoNLL-U field, treebank, sent_id, text)
- User preferences (visible columns, graph style)
- Dark mode

### Desktop App (Tauri)
- **Offline mode**: open/edit/save `.conllu` files from disk (no server needed)
- **Connected mode**: point at a BoAT server, login, full web app features
- Native file dialogs (open, save, save as)
- Keyboard shortcuts: `Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`
- Window title with dirty indicator

## API

All routes prefixed with `/api`:

| Router | Prefix | Key endpoints |
|--------|--------|---------------|
| auth | `/auth` | POST /register, POST /login, GET /me, PATCH /me |
| treebanks | `/treebanks` | CRUD, /upload, /export, /progress, /languages |
| sentences | `/sentences` | CRUD, /annotations |
| annotations | `/annotations` | CRUD, GET /by-position, GET /mine |
| wordlines | `/wordlines` | PUT /annotations/{id}/wordlines (batch update) |
| search | `/search` | GET with multi-field query |
| comments | `/comments` | CRUD per sentence |
| guidelines | `/guidelines` | CRUD per treebank |
| validation | `/validation` | Validation profiles per treebank |

Health check: `GET /health` (no `/api` prefix).
