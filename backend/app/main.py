from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import auth, songs, history, playlists

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini Spotify API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(songs.router, prefix="/api/songs", tags=["songs"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(playlists.router, prefix="/api/playlists", tags=["playlists"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
