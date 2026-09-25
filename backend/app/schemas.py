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

class PlaylistCreate(BaseModel):
    name: str

class PlaylistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)     
    id: int     
    name: str     
    user_id: int

class PlaylistSongInsert(BaseModel):
    song_id: int

class PlaylistSongOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    position: int
    playlist_id: int
    song_id: int