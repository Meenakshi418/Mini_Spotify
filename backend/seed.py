from app.database import Base, engine, SessionLocal
from app.models import Song, User
from app.security import hash_password

Base.metadata.create_all(bind=engine)

songs = [
    ("Demo Pop One", "Demo Artist A", "Pop", 2024, 95),
    ("Demo Pop Two", "Demo Artist B", "Pop", 2023, 92),
    ("Demo Rock One", "Demo Artist C", "Rock", 2022, 90),
    ("Demo Rock Two", "Demo Artist D", "Rock", 2021, 88),
    ("Demo Hip Hop One", "Demo Artist E", "Hip-Hop", 2024, 87),
    ("Demo Indie One", "Demo Artist F", "Indie", 2020, 85),
    ("Demo Electronic One", "Demo Artist G", "Electronic", 2024, 84),
    ("Demo Acoustic One", "Demo Artist H", "Acoustic", 2019, 80),
]

db = SessionLocal()

if not db.query(User).filter(User.email == "demo@minispotify.local").first():
    db.add(User(
        name="Demo User",
        email="demo@minispotify.local",
        password_hash=hash_password("demo1234")
    ))

if db.query(Song).count() == 0:
    for title, artist, genre, year, popularity in songs:
        db.add(Song(
            title=title,
            artist=artist,
            genre=genre,
            release_year=year,
            popularity=popularity
        ))

db.commit()
db.close()
print("Seed complete. Demo login: demo@minispotify.local / demo1234")
