from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import ListeningHistory, User, Song
from ..schemas import HistoryCreate

router = APIRouter()

@router.post("")
def record_history(
    payload: HistoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not db.get(Song, payload.song_id):
        raise HTTPException(status_code=404, detail="Song not found")

    event = ListeningHistory(
        user_id=user.id,
        song_id=payload.song_id,
        duration_played=payload.duration_played,
        completed=payload.completed,
    )

    db.add(event)
    db.commit()

    return {"recorded": True, "history_id": event.id}
