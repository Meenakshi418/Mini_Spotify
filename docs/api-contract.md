# Mini Spotify API Contract — Day 1

## Health
GET `/api/health`

Response:
```json
{"status":"ok"}
```

## Register
POST `/api/auth/register`

Body:
```json
{
  "name": "Demo User",
  "email": "demo@example.com",
  "password": "demo1234"
}
```

## Login
POST `/api/auth/login`

Form fields:
- username = email
- password = password

Returns:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

## Songs
GET `/api/songs`
GET `/api/songs/{song_id}`
GET `/api/songs/search?q=rock`

Song response:
```json
{
  "id": 1,
  "title": "Demo Song",
  "artist": "Demo Artist",
  "genre": "Pop",
  "youtube_video_id": null
}
```

## Like
POST `/api/songs/{song_id}/like`
DELETE `/api/songs/{song_id}/like`

Requires Bearer token.

## Listening history
POST `/api/history`

Body:
```json
{
  "song_id": 1,
  "duration_played": 30,
  "completed": false
}
```

Requires Bearer token.
