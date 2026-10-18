# Roadmap

Planned improvements for BoAT. The 2026 rewrite (FastAPI + SvelteKit + Tauri) addressed most of the critical issues from the old Django stack. Items below are what remains.

## Completed (in rewrite)

- [x] Modern frontend (SvelteKit + Svelte 5 + Tailwind CSS 4)
- [x] Async backend (FastAPI + SQLAlchemy 2.0 + asyncpg)
- [x] JWT authentication with proper security
- [x] RBAC-ready user model
- [x] CI/CD pipeline (GitLab CI)
- [x] Pre-commit hooks (ruff, shellcheck)
- [x] Comprehensive test suite (pytest-asyncio)
- [x] Type hints throughout
- [x] HTTPS via Caddy + Cloudflare Tunnel
- [x] Docker health checks and multi-stage builds
- [x] Keyboard shortcuts for annotation
- [x] Dark mode
- [x] Inline validation feedback
- [x] Dependency graph visualization (displaCy-style)
- [x] Tauri desktop app (replaces Qt app)
- [x] Offline mode for desktop (open/edit/save CoNLL-U)
- [x] Connected mode for desktop (point at a server)
- [x] FEATS editor with UD feature dropdowns
- [x] MISC editor with free-form key=value pairs

## P1 — Usability

- [ ] Undo/redo for annotation edits
- [ ] Bulk annotation operations (multi-select rows, batch status change)
- [ ] Drag-and-drop HEAD assignment on the dependency graph
- [ ] Annotation assignment workflow (admin assigns sentences to annotators)
- [ ] Cross-annotator review workflow

## P2 — Features

- [ ] UD validation profiles (configurable per treebank)
- [ ] Real-time multi-user collaboration (WebSocket)
- [ ] Notification system for annotation assignments
- [ ] Diff view between annotator versions in agreement page
- [ ] Export options: CoNLL-U, JSON, TSV
- [ ] Public demo instance

## P3 — Infrastructure

- [ ] Database backup/restore scripts
- [ ] Performance monitoring (Sentry)
- [ ] API rate limiting
- [ ] Pagination for large treebanks (currently loads all sentences)
- [ ] macOS and Windows builds for desktop app (CI)

## P4 — Dissemination

- [ ] Write and submit a journal/conference paper on the 2026 rewrite (architecture + features)
- [ ] Public release of the unified BoAT (web+desktop) under **boun-tabi/boat** (replacing legacy)
- [ ] Update [Universal Dependencies tools](https://universaldependencies.org/tools#boat) link and reference the new paper
- [ ] Updated user documentation / tutorial
- [ ] Public release of desktop app binaries (macOS, Windows, Linux)
