# Mini Spotify — Day 1 Starter

Goal for today: get a live vertical slice working.

## Stack
- Frontend: React + Vite
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Auth: JWT
- Playback: YouTube IFrame Player API
- Data/ML: Pandas + scikit-learn

## Today's demo target
1. Register/login
2. Browse seeded songs
3. Search songs
4. Play a song through a YouTube embed
5. Like a song
6. Record a listening event
7. Show `/docs` for the API

## Repository structure
- `frontend/` React app
- `backend/` FastAPI app
- `dwm/` DWM/ML work for Person 3
- `data/` raw/processed/sample data
- `docs/` architecture and API contract

## Quick start

### Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

For the first demo, the backend can use SQLite by default. Before live deployment, set `DATABASE_URL` to PostgreSQL.

### Frontend
```powershell
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Team rule
Do not redesign the folder structure or API names without telling Person 1.
