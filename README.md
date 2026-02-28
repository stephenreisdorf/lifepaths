# Lifepaths

Full-stack app with a FastAPI backend and Vue 3 frontend.

## Project Structure

```
lifepaths/
├── backend/       # FastAPI Python API
│   ├── main.py
│   ├── .env
│   ├── .python-version
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/      # Vue 3 + Vite app
│   ├── src/
│   │   └── App.vue
│   └── package.json
└── README.md
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) v18+

## Running the App

Open two terminal windows/tabs from the project root.

### Terminal 1 — Backend

```bash
cd backend
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

| Route | Description |
|---|---|
| `GET /` | Root welcome message |
| `GET /api/health` | Returns `{ "status": "ok" }` |

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

The Vue app will be available at `http://localhost:5173`.

## Environment Variables

Add any backend secrets to `backend/.env`. The file is loaded automatically via `python-dotenv`.
