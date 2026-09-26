from app.database import SessionLocal
from app.models import User
from app.security import hash_password

EMAIL = "admin@minispotify.local"
PASSWORD = "Admin1234!"
NAME = "Mini Spotify Admin"

db = SessionLocal()

try:
    existing = db.query(User).filter(User.email == EMAIL).first()

    if existing:
        existing.role = "admin"
        db.commit()
        print("Existing user promoted to admin.")
    else:
        user = User(
            name=NAME,
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            role="admin",
        )

        db.add(user)
        db.commit()

        print("Admin created.")
finally:
    db.close()