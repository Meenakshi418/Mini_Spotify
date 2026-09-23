import { useEffect, useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function App() {
  const [songs, setSongs] = useState([])
  const [q, setQ] = useState('')
  const [selected, setSelected] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [status, setStatus] = useState('')

  async function loadSongs(search = '') {
    const url = search ? `${API}/api/songs/search?q=${encodeURIComponent(search)}` : `${API}/api/songs`
    const res = await axios.get(url)
    setSongs(res.data)
  }

  useEffect(() => { loadSongs() }, [])

  async function loginDemo() {
    const form = new URLSearchParams()
    form.append('username', 'demo@minispotify.local')
    form.append('password', 'demo1234')
    const res = await axios.post(`${API}/api/auth/login`, form)
    localStorage.setItem('token', res.data.access_token)
    setToken(res.data.access_token)
    setStatus('Logged in as demo user')
  }

  async function likeSong(song) {
    if (!token) return setStatus('Click Demo Login first')
    await axios.post(`${API}/api/songs/${song.id}/like`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    })
    setStatus(`Liked "${song.title}"`)
  }

  async function recordPlay(song) {
    if (!token) return
    await axios.post(`${API}/api/history`, {
      song_id: song.id,
      duration_played: 0,
      completed: false
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
  }

  return (
    <div className="page">
      <header>
        <div>
          <h1>🎵 Mini Spotify</h1>
          <p>Day 1 live demo build</p>
        </div>
        <button onClick={loginDemo}>{token ? 'Logged in' : 'Demo Login'}</button>
      </header>

      <section className="search">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Search songs, artists or genres..."
        />
        <button onClick={() => loadSongs(q)}>Search</button>
      </section>

      {status && <div className="status">{status}</div>}

      <div className="grid">
        {songs.map(song => (
          <article className="card" key={song.id}>
            <div className="cover">♪</div>
            <h3>{song.title}</h3>
            <p>{song.artist} · {song.genre}</p>
            <p className="muted">Popularity: {song.popularity}</p>
            <div className="actions">
              <button onClick={() => { setSelected(song); recordPlay(song) }}>▶ Play</button>
              <button onClick={() => likeSong(song)}>♥ Like</button>
            </div>
          </article>
        ))}
      </div>

      {selected && (
        <div className="player">
          <div>
            <strong>{selected.title}</strong>
            <span>{selected.artist}</span>
          </div>
          {selected.youtube_video_id ? (
            <iframe
              width="480"
              height="270"
              src={`https://www.youtube.com/embed/${selected.youtube_video_id}`}
              title={selected.title}
              allow="autoplay; encrypted-media; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <div className="placeholder">
              Add a verified YouTube video ID to this song to enable playback.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
