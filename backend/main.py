from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from content.loader import load_all_configs
from routers import characters, content, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load and validate all LifePathConfig files at startup; fail fast on errors
    configs = load_all_configs()
    print(f"Loaded {len(configs)} life path config(s): {list(configs.keys())}")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(content.router)
app.include_router(characters.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Lifepaths API"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
