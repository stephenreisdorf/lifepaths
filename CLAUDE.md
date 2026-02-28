# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Backend**: FastAPI (Python 3.12), managed with `uv`
- **Frontend**: Vue 3 + Vite, managed with `npm`

## Commands

### Backend (run from `backend/`)

```bash
uv run uvicorn main:app --reload   # Start dev server at http://localhost:8000
```

### Frontend (run from `frontend/`)

```bash
npm run dev       # Start dev server at http://localhost:5173
npm run build     # Production build to dist/
npm run preview   # Preview production build
```

No test framework is configured yet.

## Architecture

Monorepo with independent backend and frontend directories. Both must run simultaneously during development.

### Backend (`backend/`)

- Entry point: `main.py` — single FastAPI app instance
- CORS is configured to allow `http://localhost:5173` only
- Environment variables loaded from `backend/.env` via `python-dotenv`

### Frontend (`frontend/`)

- Entry point: `src/main.js` → mounts `App.vue` to `#app`
- Uses Vue 3 Composition API (`<script setup>` SFC syntax)
- Axios makes requests directly to `http://localhost:8000` (hardcoded in dev)
- No router or state management library — add as needed

## Environment Variables

Add backend secrets to `backend/.env`. The file is gitignored and loaded automatically at startup.
