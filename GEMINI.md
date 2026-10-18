# BoAT Project Instructions

This file contains team-shared architecture, conventions, and workflows for the BoAT project.

## Project State
- **Current Version (2026):** Full rework completed. The application is now split into a FastAPI backend, a SvelteKit frontend, and a Tauri v2 desktop shell.
- **Legacy Components:** All Django (web) and PySide6 (desktop) code has been removed and archived in `tubitak-sources.zip` and `altnlp-2022-sources.zip`.

## Strategic Intent
- **Release Strategy:** The 2026 rework is currently in a private development phase. The planned sequence is:
    1. Finalize the rework and ensure stability.
    2. Author and publish a paper describing the new architecture and features (FastAPI/SvelteKit/Tauri).
    3. Release the code publicly under the **boun-tabi/boat** repository, replacing the legacy version.
    4. Update external references (e.g., Universal Dependencies tools page) to point to the new public repository and the new publication.

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16.
- **Frontend:** SvelteKit 2, Svelte 5 (runes), Tailwind CSS 4.
- **Desktop:** Tauri v2 (Rust), sharing the SvelteKit frontend.
- **Auth:** JWT-based authentication.

## Development Workflow
- **Linting:** Use `ruff` for the backend and `svelte-check` for the frontend.
- **Testing:** Use `pytest` with `pytest-asyncio` for the backend.
