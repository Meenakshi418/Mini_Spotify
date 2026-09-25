from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import Like, Song, User
from ..schemas import SongOut

router = APIRouter()

@router.get("", response_model=list[SongOut])
def list_songs(db: Session = Depends(get_db), limit: int = Query(30, ge=1, le=100)):
    return db.query(Song).order_by(Song.popularity.desc()).limit(limit).all()

@router.get("/search", response_model=list[SongOut])
def search_songs(q: str = "", db: Session = Depends(get_db)):
    term = f"%{q}%"
    return (
        db.query(Song)
        .filter((Song.title.ilike(term)) | (Song.artist.ilike(term)) | (Song.genre.ilike(term)))
        .order_by(Song.popularity.desc())
        .limit(50)
        .all()
    )

@router.get("/liked")
def get_liked_songs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    likes = (
        db.query(Like)
        .filter(Like.user_id == user.id)
        .all()
    )

    return [like.song_id for like in likes]

@router.get("/{song_id}", response_model=SongOut)
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song

@router.post("/{song_id}/like")
def like_song(song_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.get(Song, song_id):
        raise HTTPException(status_code=404, detail="Song not found")
    existing = db.query(Like).filter(Like.user_id == user.id, Like.song_id == song_id).first()
    if not existing:
        db.add(Like(user_id=user.id, song_id=song_id))
        db.commit()
    return {"liked": True}

@router.delete("/{song_id}/like")
def unlike_song(song_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing = db.query(Like).filter(Like.user_id == user.id, Like.song_id == song_id).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {"liked": False}
