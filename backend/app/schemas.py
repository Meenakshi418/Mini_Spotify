from pydantic import BaseModel, ConfigDict

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SongOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    artist: str
    genre: str
    release_year: int | None = None
    popularity: float
    youtube_video_id: str | None = None

class HistoryCreate(BaseModel):
    song_id: int
    duration_played: float
    completed: bool = False
