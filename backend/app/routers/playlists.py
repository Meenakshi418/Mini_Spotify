from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import Playlist, User, PlaylistSong
from ..schemas import PlaylistCreate, PlaylistOut, PlaylistSongInsert, PlaylistSongOut

router = APIRouter()


@router.post("", response_model=PlaylistOut)
def create_playlist(payload: PlaylistCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = Playlist(
        name=payload.name,
        user_id=user.id
    )

    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return playlist


@router.get("", response_model=list[PlaylistOut])
def show_playlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Playlist)
        .filter(Playlist.user_id == user.id)
        .order_by(Playlist.created_at.desc())
        .all()
    )


@router.post("/{playlist_id}/songs", response_model=PlaylistSongOut)
def insert_playlist_song(playlist_id: int, payload: PlaylistSongInsert, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    playlist = (
        db.query(Playlist)
        .filter(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
        .first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    existing_count = (
        db.query(PlaylistSong)
        .filter(PlaylistSong.playlist_id == playlist_id)
        .count()
    )

    playlist_song = PlaylistSong(
        playlist_id=playlist_id,
        song_id=payload.song_id,
        position=existing_count + 1
    )

    db.add(playlist_song)
    db.commit()
    db.refresh(playlist_song)

    return playlist_song


@router.get("/{playlist_id}/songs", response_model=list[PlaylistSongOut])
def view_playlist_song(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    playlist = (
        db.query(Playlist)
        .filter(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
        .first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return (
        db.query(PlaylistSong)
        .filter(PlaylistSong.playlist_id == playlist_id)
        .order_by(PlaylistSong.position)
        .all()
    )


@router.delete("/{playlist_id}/songs/{song_id}")
def delete_song_playlist(
    playlist_id: int,
    song_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    playlist = (
        db.query(Playlist)
        .filter(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
        .first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    existing = (
        db.query(PlaylistSong)
        .filter(
            PlaylistSong.playlist_id == playlist_id,
            PlaylistSong.song_id == song_id
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Song not found in playlist")

    db.delete(existing)
    db.commit()

    return {"deleted": True}

@router.delete("/{playlist_id}")
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    playlist = (
        db.query(Playlist)
        .filter(
            Playlist.id == playlist_id,
            Playlist.user_id == user.id
        )
        .first()
    )

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    db.query(PlaylistSong).filter(
        PlaylistSong.playlist_id == playlist_id
    ).delete()

    db.delete(playlist)
    db.commit()

    return {"deleted": True}