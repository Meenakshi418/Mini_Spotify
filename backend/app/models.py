from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")

class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    artist = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=False, index=True)
    release_year = Column(Integer, nullable=True)
    popularity = Column(Float, default=0)
    youtube_video_id = Column(String(50), nullable=True)

class ListeningHistory(Base):
    __tablename__ = "listening_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    duration_played = Column(Float, default=0)
    completed = Column(Boolean, default=False)
    liked = Column(Boolean, default=False)

class Like(Base):
    __tablename__ = "likes"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    song_id = Column(Integer, ForeignKey("songs.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Playlist(Base):
    __tablename__="playlists"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PlaylistSong(Base):
    __tablename__="playlist_songs"
    playlist_id = Column(Integer, ForeignKey("playlists.id"), primary_key=True, nullable=False, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"), primary_key=True, nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)

    