# BoAT - Boğaziçi University Annotation Tool

Collaborative tool for linguistic annotation and treebank management using the [Universal Dependencies](https://universaldependencies.org/) framework.

**Project Status:** This is the **2026 rework** (FastAPI + SvelteKit + Tauri). Once development is finalized, this unified version will be moved to a Boğaziçi organization repository, replacing the original [boun-tabi/BoAT](https://github.com/boun-tabi/BoAT).

**Repo:** [GitLab](https://gitlab.com/furkan5204/boat)

## Pages

- [Current Status](current-status) — Architecture, tech stack, features
- [Development](development) — Setup, running, deployment
- [Roadmap](roadmap) — Planned improvements

## Overview

BoAT provides two ways to annotate:

| Mode | Description |
|------|-------------|
| **Web app** | Multi-user server deployment (FastAPI + SvelteKit + PostgreSQL) |
| **Desktop app** | Tauri v2 — offline `.conllu` editing or connect to a server |

## Quick Links

| Component | Path | Tech |
|-----------|------|------|
| Backend | `backend/` | FastAPI, SQLAlchemy 2.0 (async), PostgreSQL |
| Frontend | `frontend/` | SvelteKit 2, Svelte 5, TypeScript, Tailwind CSS 4 |
| Desktop | `frontend/src-tauri/` | Tauri v2 (Rust) |
| Papers | `papers/` | LaTeX (AltNLP, TUBITAK) |
| Infra | `docker-compose.yml`, `Caddyfile` | Docker Compose, Caddy |

## History

- **2021–2024:** Django + jQuery web app (`app/`) + PySide6 desktop app (`app-qt/`)
- **2026:** Full rewrite to FastAPI + SvelteKit + Tauri (current version)
- **Origin:** [boun-tabi/BoAT](https://github.com/boun-tabi/BoAT) (original Qt tool)
