import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import Dashboard from "./Dashboard";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  /* =====================================================
     CORE STATE
     ===================================================== */

  const [songs, setSongs] = useState([]);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(null);

  const [token, setToken] = useState(localStorage.getItem("token") || "");

  const [likedSongs, setLikedSongs] = useState([]);

  const [playlists, setPlaylists] = useState([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState(null);
  const [playlistSongs, setPlaylistSongs] = useState([]);

  const [youtubeAPIReady, setYoutubeAPIReady] = useState(false);
  const [youtubePlaying, setYoutubePlaying] = useState(false);
  const [youtubeProgress, setYoutubeProgress] = useState(0);

  const [loading, setLoading] = useState(true);
  const [loggingIn, setLoggingIn] = useState(false);
  const [likingId, setLikingId] = useState(null);

  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const [isSearching, setIsSearching] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);

  const searchInputRef = useRef(null);
  const youtubePlayerRef = useRef(null);
  const youtubeContainerRef = useRef(null);

  /* =====================================================
     LOAD SONGS
     ===================================================== */

  async function loadSongs(search = "") {
    try {
      setLoading(true);
      setError("");

      const cleanSearch = search.trim();

      const url = cleanSearch
        ? `${API}/api/songs/search?q=${encodeURIComponent(cleanSearch)}`
        : `${API}/api/songs`;

      const res = await axios.get(url);

      const incomingSongs = Array.isArray(res.data) ? res.data : [];

      setSongs(incomingSongs);
    } catch (err) {
      console.error("Song loading error:", err);

      setSongs([]);

      setError(
        "Unable to load songs. Please make sure the backend is running.",
      );
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  }

  /* =================================================
     LOAD PLAYLISTS
     ================================================= */

  async function loadPlaylists() {
    if (!token) return;

    try {
      const res = await axios.get(`${API}/api/playlists`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setPlaylists(res.data);
    } catch (err) {
      console.error("Playlist loading error:", err);
    }
  }

  /* =================================================
     CREATE PLAYLIST
     ================================================= */

  async function createPlaylist() {
    if (!token) {
      setStatus("Please log in first");
      return;
    }

    const name = window.prompt("Enter playlist name:");

    if (!name?.trim()) return;

    try {
      await axios.post(
        `${API}/api/playlists`,
        { name: name.trim() },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      await loadPlaylists();
      setStatus("Playlist created");
    } catch (err) {
      console.error("Playlist creation error:", err);
      setStatus("Unable to create playlist");
    }
  }

  /* =================================================
     LOAD PLAYLIST SONGS
     ================================================= */

  async function loadPlaylistSongs(playlistId) {
    if (!token) return;

    try {
      const res = await axios.get(
        `${API}/api/playlists/${playlistId}/songs`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      setPlaylistSongs(res.data);
    } catch (err) {
      console.error("Playlist songs loading error:", err);
      setPlaylistSongs([]);
    }
  }

  /* =================================================
     SELECT PLAYLIST
     ================================================= */

  async function selectPlaylist(playlist) {
    setSelectedPlaylist(playlist);
    await loadPlaylistSongs(playlist.id);
  }

  /* =================================================
     ADD SONG TO PLAYLIST
     ================================================= */

  async function addSongToPlaylist(song) {
    if (!token) {
      setStatus("Please log in first");
      return;
    }

    if (playlists.length === 0) {
      setStatus("Create a playlist first");
      return;
    }

    const playlistChoices = playlists
      .map((playlist, index) => `${index + 1}. ${playlist.name}`)
      .join("\n");

    const choice = window.prompt(
      `Add "${song.title}" to which playlist?\n\n${playlistChoices}\n\nEnter number:`
    );

    if (choice === null) {
      setStatus("Add cancelled");
      return;
    }

    const index = Number(choice) - 1;

    if (
      !Number.isInteger(index) ||
      index < 0 ||
      index >= playlists.length
    ) {
      setStatus("Invalid playlist number");
      return;
    }

    const playlist = playlists[index];

    setStatus(`Adding "${song.title}"...`);

    try {
      const res = await axios.post(
        `${API}/api/playlists/${playlist.id}/songs`,
        {
          song_id: song.id,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      console.log("Add response:", res.data);

      setStatus(`✓ Added "${song.title}" to "${playlist.name}"`);

      if (selectedPlaylist?.id === playlist.id) {
        await loadPlaylistSongs(playlist.id);
      }
    } catch (err) {
      console.error("Add to playlist error:", err);
      console.error("Backend response:", err.response?.data);

      setStatus(
        err.response?.data?.detail ||
        "Could not add song to playlist"
      );
    }
  }

  /* =================================================
     REMOVE SONG FROM PLAYLIST
     ================================================= */

  async function removeSongFromPlaylist(songId) {
    if (!selectedPlaylist) return;

    try {
      await axios.delete(
        `${API}/api/playlists/${selectedPlaylist.id}/songs/${songId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      await loadPlaylistSongs(selectedPlaylist.id);
      setStatus("Song removed from playlist");
    } catch (err) {
      console.error("Remove playlist song error:", err);
      setStatus("Unable to remove song");
    }
  }

  /* =================================================
     DELETE PLAYLIST
     ================================================= */

  async function deletePlaylist(playlistId) {
    if (!token) return;

    const playlist = playlists.find((item) => item.id === playlistId);

    if (!playlist) return;

    const confirmed = window.confirm(
      `Delete playlist "${playlist.name}"?`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/api/playlists/${playlistId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (selectedPlaylist?.id === playlistId) {
        setSelectedPlaylist(null);
        setPlaylistSongs([]);
      }

      await loadPlaylists();
      setStatus("Playlist deleted");
    } catch (err) {
      console.error("Delete playlist error:", err);
      setStatus("Unable to delete playlist");
    }
  }

  /* =================================================
     YOUTUBE IFRAME API
     ================================================= */

  useEffect(() => {
    if (window.YT?.Player) {
      setYoutubeAPIReady(true);
      return;
    }

    const existingScript = document.getElementById("youtube-iframe-api");

    if (existingScript) {
      window.onYouTubeIframeAPIReady = () => {
        setYoutubeAPIReady(true);
      };
      return;
    }

    const script = document.createElement("script");

    script.id = "youtube-iframe-api";
    script.src = "https://www.youtube.com/iframe_api";

    window.onYouTubeIframeAPIReady = () => {
      setYoutubeAPIReady(true);
    };

    document.body.appendChild(script);
  }, []);

  /* =================================================
     CREATE YOUTUBE PLAYER
     ================================================= */

  useEffect(() => {
    if (
      !selected?.youtube_video_id ||
      !youtubeAPIReady ||
      !youtubeContainerRef.current
    ) {
      return;
    }

    if (youtubePlayerRef.current) {
      youtubePlayerRef.current.destroy();
      youtubePlayerRef.current = null;
    }

    youtubePlayerRef.current = new window.YT.Player(
      youtubeContainerRef.current,
      {
        videoId: selected.youtube_video_id,
        playerVars: {
          autoplay: 1,
          controls: 1,
          playsinline: 1,
          rel: 0,
          origin: window.location.origin,
        },
        events: {
          onReady: (event) => {
            event.target.playVideo();
          },
          onStateChange: (event) => {
            if (event.data === window.YT.PlayerState.PLAYING) {
              setYoutubePlaying(true);
            }

            if (
              event.data === window.YT.PlayerState.PAUSED ||
              event.data === window.YT.PlayerState.ENDED
            ) {
              setYoutubePlaying(false);
            }
          },
        },
      },
    );

    return () => {
      if (youtubePlayerRef.current) {
        youtubePlayerRef.current.destroy();
        youtubePlayerRef.current = null;
      }
    };
  }, [selected?.youtube_video_id, youtubeAPIReady]);

  /* =================================================
     YOUTUBE PROGRESS
     ================================================= */

  useEffect(() => {
    if (!selected?.youtube_video_id || !youtubeAPIReady) {
      setYoutubeProgress(0);
      return;
    }

    const timer = setInterval(() => {
      const player = youtubePlayerRef.current;

      if (!player?.getCurrentTime || !player?.getDuration) {
        return;
      }

      const duration = player.getDuration();

      if (duration > 0) {
        const currentTime = player.getCurrentTime();
        const progress = (currentTime / duration) * 100;

        setYoutubeProgress(Math.min(Math.max(progress, 0), 100));
      }
    }, 500);

    return () => clearInterval(timer);
  }, [selected?.youtube_video_id, youtubeAPIReady]);

  /* =====================================================
     INITIAL LOAD
     ===================================================== */

  useEffect(() => {
    loadSongs();
  }, []);

  useEffect(() => {
    if (token) {
      loadPlaylists();
      loadLikedSongs();
    }
  }, [token]);

  /* =====================================================
     STATUS AUTO HIDE
     ===================================================== */

  useEffect(() => {
    if (!status) return;

    const timer = setTimeout(() => {
      setStatus("");
    }, 3500);

    return () => clearTimeout(timer);
  }, [status]);

  /* =====================================================
     GLOBAL KEYBOARD CONTROLS
     ===================================================== */

  useEffect(() => {
    function handleKeyDown(event) {
      const tag = event.target?.tagName?.toLowerCase();

      const typing =
        tag === "input" ||
        tag === "textarea" ||
        event.target?.isContentEditable;

      /* Escape = close player */
      if (event.key === "Escape") {
        setSelected(null);
        return;
      }

      /* "/" = focus search */
      if (event.key === "/" && !typing) {
        event.preventDefault();

        searchInputRef.current?.focus();

        setStatus("Search focused");
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  /* =====================================================
     DEMO LOGIN
     ===================================================== */

  async function loginDemo() {
    if (loggingIn) return;

    try {
      setLoggingIn(true);
      setError("");

      const form = new URLSearchParams();

      form.append("username", "demo@minispotify.local");

      form.append("password", "demo1234");

      const res = await axios.post(`${API}/api/auth/login`, form);

      const accessToken = res.data.access_token;

      localStorage.setItem("token", accessToken);

      setToken(accessToken);

      setStatus("✓ Welcome back, Demo User");
    } catch (err) {
      console.error("Login error:", err);

      setStatus("Login failed. Please make sure the backend is running.");
    } finally {
      setLoggingIn(false);
    }
  }

  /* =====================================================
     LOAD LIKED SONGS
     ===================================================== */

  async function loadLikedSongs() {
    if (!token) return;

    try {
      const res = await axios.get(`${API}/api/songs/liked`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setLikedSongs(res.data);
    } catch (err) {
      console.error("Liked songs loading error:", err);
    }
  }

  /* =====================================================
     LIKE / UNLIKE SONG
     ===================================================== */

  async function likeSong(song) {
    if (!token) {
      setStatus("Please click Demo Login first");
      return;
    }

    if (likingId === song.id) {
      return;
    }

    try {
      setLikingId(song.id);

      if (likedSongs.includes(song.id)) {
        await axios.delete(
          `${API}/api/songs/${song.id}/like`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        );

        setLikedSongs((prev) => prev.filter((id) => id !== song.id));
        setStatus(`♡ Removed "${song.title}" from your likes`);
      } else {
        await axios.post(
          `${API}/api/songs/${song.id}/like`,
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        );

        setLikedSongs((prev) => [...prev, song.id]);
        setStatus(`♥ Added "${song.title}" to your likes`);
      }
    } catch (err) {
      console.error("Like/unlike error:", err);

      setStatus(
        err.response?.data?.detail ||
        "Unable to update like"
      );
    } finally {
      setLikingId(null);
    }
  }

  /* =====================================================
     RECORD PLAY HISTORY
     ===================================================== */

  async function recordPlay(song) {
    if (!token) return;

    try {
      await axios.post(
        `${API}/api/history`,
        {
          song_id: song.id,
          duration_played: 0,
          completed: false,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );
    } catch (err) {
      console.error("Play history error:", err);
    }
  }

  /* =====================================================
     PLAY SONG
     ===================================================== */

  function playSong(song) {
    setSelected(song);
    setYoutubePlaying(false);
    setYoutubeProgress(0);

    recordPlay(song);

    setStatus(`▶ Now playing "${song.title}"`);
  }

  /* =================================================
     TOGGLE YOUTUBE PLAYBACK
     ================================================= */

  function toggleYouTubePlayback() {
    const player = youtubePlayerRef.current;

    if (!player || !window.YT) return;

    const state = player.getPlayerState();

    if (state === window.YT.PlayerState.PLAYING) {
      player.pauseVideo();
    } else {
      player.playVideo();
    }
  }

  /* =====================================================
     SEARCH
     ===================================================== */

  function handleSearch() {
    const cleanQuery = q.trim();

    setIsSearching(true);

    loadSongs(cleanQuery);
  }

  function handleSearchKeyDown(event) {
    if (event.key === "Enter") {
      handleSearch();
    }

    if (event.key === "Escape") {
      event.target.blur();
    }
  }

  /* =====================================================
     CLEAR SEARCH
     ===================================================== */

  function clearSearch() {
    setQ("");
    setError("");

    loadSongs();

    searchInputRef.current?.focus();
  }

  /* =====================================================
     LOGOUT
     ===================================================== */

  function logoutDemo() {
    localStorage.removeItem("token");

    setToken("");
    setLikedSongs([]);
    setPlaylists([]);
    setSelectedPlaylist(null);
    setPlaylistSongs([]);
    setSelected(null);

    setStatus("Signed out of Demo User");
  }

  /* =====================================================
     CLOSE PLAYER
     ===================================================== */

  function closePlayer() {
    setSelected(null);
  }

  /* =====================================================
     DERIVED DATA
     ===================================================== */

  const totalSongs = songs.length;

  const totalLiked = likedSongs.length;

  const averagePopularity = useMemo(() => {
    if (!songs.length) return 0;

    const total = songs.reduce(
      (sum, song) =>
        sum + Math.min(Math.max(Number(song.popularity) || 0, 0), 100),
      0,
    );

    return Math.round(total / songs.length);
  }, [songs]);

  const genres = useMemo(() => {
    return new Set(songs.map((song) => song.genre).filter(Boolean)).size;
  }, [songs]);

  const activeSongIndex = useMemo(() => {
    if (!selected) return -1;

    return songs.findIndex((song) => song.id === selected.id);
  }, [songs, selected]);

  /* =====================================================
     NEXT SONG
     ===================================================== */

  function playNextSong() {
    if (!songs.length) return;

    const nextIndex =
      activeSongIndex >= 0
        ? (activeSongIndex + 1) % songs.length
        : 0;

    const nextSong = songs[nextIndex];

    setSelected(nextSong);
    setYoutubePlaying(false);
    setYoutubeProgress(0);

    recordPlay(nextSong);

    setStatus(`▶ Now playing "${nextSong.title}"`);
  }

  /* =====================================================
     PREVIOUS SONG
     ===================================================== */

  function playPreviousSong() {
    if (!songs.length) return;

    const previousIndex =
      activeSongIndex > 0
        ? activeSongIndex - 1
        : songs.length - 1;

    const previousSong = songs[previousIndex];

    setSelected(previousSong);
    setYoutubePlaying(false);
    setYoutubeProgress(0);

    recordPlay(previousSong);

    setStatus(`▶ Now playing "${previousSong.title}"`);
  }

  /* =====================================================
     RENDER
     ===================================================== */

  return (
    <div className={`page ${showDashboard ? "dashboard-mode" : ""}`}>
      {/* =================================================
          AMBIENT BACKGROUND
          ================================================= */}

      <div className="ambient ambient-one" aria-hidden="true" />

      <div className="ambient ambient-two" aria-hidden="true" />

      <div className="ambient ambient-three" aria-hidden="true" />

      {/* =================================================
          HEADER
          ================================================= */}

      <header className="site-header">
        <div className="brand">
          <div className="brand-icon" aria-hidden="true">
            ♫
          </div>

          <div className="brand-copy">
            <div className="brand-eyebrow">MUSIC • DISCOVER • PLAY</div>

            <h1>
              Mini <span>Spotify</span>
            </h1>

            <p>Discover music. Play. Like. Enjoy.</p>
          </div>
        </div>

        <div className="header-actions">
          <button
            className={`dashboard-button ${showDashboard ? "dashboard-active" : ""}`}
            type="button"
            onClick={() => setShowDashboard((prev) => !prev)}
          >
            <span>◈</span>
            {showDashboard ? "Library" : "Analytics"}
          </button>
          <button
            className="shortcut-hint"
            type="button"
            onClick={() => searchInputRef.current?.focus()}
            title="Focus search"
          >
            <span>⌕</span>
            <kbd>/</kbd>
          </button>

          <button
            className={`login-button ${token ? "logged-in" : ""}`}
            onClick={token ? logoutDemo : loginDemo}
            disabled={loggingIn}
            title={token ? "Click to sign out" : "Sign in with demo account"}
          >
            <span className="login-dot" />

            {loggingIn ? "Signing In..." : token ? "✓ Logged In" : "Demo Login"}
          </button>
        </div>
      </header>
      {showDashboard && <Dashboard />}

      {/* =================================================
          HERO / LIBRARY INTRO
          ================================================= */}

      <section className="library-hero">
        <div className="hero-copy">
          <div className="section-kicker">
            <span className="kicker-line" />
            YOUR MUSIC LIBRARY
          </div>

          <h2>
            Discover
            <span> Music</span>
          </h2>

          <p>Explore your collection and find something worth playing.</p>
        </div>

        <div className="library-stats">
          <button
            className={`stat-card ${showStats ? "stat-active" : ""}`}
            type="button"
            onClick={() => setShowStats((prev) => !prev)}
          >
            <span className="stat-icon">♪</span>

            <span className="stat-value">{totalSongs}</span>

            <span className="stat-label">Songs</span>
          </button>

          <div className="stat-card">
            <span className="stat-icon">♡</span>

            <span className="stat-value">{totalLiked}</span>

            <span className="stat-label">Liked</span>
          </div>

          <div className="stat-card">
            <span className="stat-icon">◈</span>

            <span className="stat-value">{genres}</span>

            <span className="stat-label">Genres</span>
          </div>
        </div>
      </section>

      {/* =================================================
          OPTIONAL STATS PANEL
          ================================================= */}

      {showStats && !loading && (
        <section className="stats-panel">
          <div className="stats-panel-item">
            <span>Library size</span>
            <strong>{totalSongs} songs</strong>
          </div>

          <div className="stats-panel-item">
            <span>Average popularity</span>
            <strong>{averagePopularity}/100</strong>
          </div>

          <div className="stats-panel-item">
            <span>Available genres</span>
            <strong>{genres}</strong>
          </div>

          <div className="stats-panel-item">
            <span>Session</span>
            <strong>{token ? "Authenticated" : "Guest"}</strong>
          </div>
        </section>
      )}

      {/* =================================================
          SEARCH
          ================================================= */}

      <section className="search-section">
        <div className="search-heading-row">
          <div>
            <span className="search-eyebrow">SEARCH LIBRARY</span>

            <span className="search-count">
              {loading
                ? "Finding songs..."
                : `${songs.length} ${songs.length === 1 ? "song" : "songs"}`}
            </span>
          </div>

          {q && (
            <button
              className="clear-search-text"
              onClick={clearSearch}
              type="button"
            >
              Clear search
            </button>
          )}
        </div>

        <div className="search">
          <span className="search-icon" aria-hidden="true">
            ⌕
          </span>

          <input
            ref={searchInputRef}
            value={q}
            onChange={(event) => setQ(event.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search songs, artists or genres..."
            aria-label="Search songs, artists or genres"
          />

          {q && (
            <button
              className="clear-button"
              onClick={clearSearch}
              aria-label="Clear search"
              type="button"
            >
              ×
            </button>
          )}

          <button
            className="search-button"
            onClick={handleSearch}
            disabled={loading}
            type="button"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>
      </section>

      {/* =================================================
          STATUS
          ================================================= */}

      {status && (
        <div className="status" role="status" aria-live="polite">
          <span className="status-pulse">●</span>

          <span>{status}</span>

          <button
            type="button"
            onClick={() => setStatus("")}
            aria-label="Dismiss message"
          >
            ×
          </button>
        </div>
      )}

      {/* =================================================
          ERROR
          ================================================= */}

      {error && (
        <div className="error-message" role="alert">
          <span>⚠</span>

          <div>
            <strong>Something went wrong</strong>

            <p>{error}</p>
          </div>

          <button type="button" onClick={() => loadSongs(q)}>
            Retry
          </button>
        </div>
      )}

      {/* =================================================
          PLAYLISTS
          ================================================= */}

      <section className="playlists-section">
        <div className="search-heading-row">
          <div>
            <span className="search-eyebrow">YOUR PLAYLISTS</span>
          </div>
        </div>

        <button type="button" onClick={createPlaylist}>
          + Create Playlist
        </button>

        {playlists.length === 0 ? (
          <p>No playlists yet.</p>
        ) : (
          <div className="playlists-list">
            {playlists.map((playlist) => (
              <div
                className={`playlist-item ${
                  selectedPlaylist?.id === playlist.id
                    ? "playlist-active"
                    : ""
                }`}
                key={playlist.id}
              >
                <button
                  type="button"
                  onClick={() => selectPlaylist(playlist)}
                >
                  {playlist.name}
                </button>

                <button
                  type="button"
                  className="playlist-delete"
                  onClick={() => deletePlaylist(playlist.id)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {selectedPlaylist && (
          <div className="selected-playlist">
            <div className="selected-playlist-header">
              <div>
                <span className="search-eyebrow">SELECTED PLAYLIST</span>
                <h3>{selectedPlaylist.name}</h3>
              </div>
            </div>

            {playlistSongs.length === 0 ? (
              <p>No songs in this playlist yet.</p>
            ) : (
              <div className="playlist-song-list">
                {playlistSongs.map((playlistSong) => {
                  const song = songs.find(
                    (item) => item.id === playlistSong.song_id
                  );

                  if (!song) return null;

                  return (
                    <div
                      className="playlist-song"
                      key={`${playlistSong.playlist_id}-${playlistSong.song_id}`}
                    >
                      <div>
                        <strong>{song.title}</strong>
                        <span>{song.artist}</span>
                      </div>

                      <button
                        type="button"
                        onClick={() => playSong(song)}
                      >
                        ▶
                      </button>

                      <button
                        type="button"
                        onClick={() => removeSongFromPlaylist(song.id)}
                      >
                        Remove
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </section>

      {/* =================================================
          MUSIC AREA
          ================================================= */}

      <main>
        {loading ? (
          /* =================================================
             LOADING
             ================================================= */

          <div className="loading">
            <div className="loading-orb">
              <div className="spinner" />
            </div>

            <h3>Loading your music</h3>

            <p>Preparing your library...</p>
          </div>
        ) : songs.length === 0 ? (
          /* =================================================
             EMPTY
             ================================================= */

          <div className="empty-state">
            <div className="empty-icon">♫</div>

            <span className="section-kicker">NO RESULTS</span>

            <h2>Nothing found</h2>

            <p>We couldn't find anything matching your search.</p>

            <button onClick={clearSearch} type="button">
              <span>↻</span>
              Show All Songs
            </button>
          </div>
        ) : (
          /* =================================================
             SONG GRID
             ================================================= */

          <div className="grid">
            {songs.map((song, index) => {
              const isLiked = likedSongs.includes(song.id);

              const isPlaying = selected?.id === song.id;

              const popularity = Math.min(
                Math.max(Number(song.popularity) || 0, 0),
                100,
              );

              return (
                <article
                  className={`card ${isPlaying ? "active-card" : ""} ${
                    isLiked ? "liked-card" : ""
                  }`}
                  key={song.id}
                >
                  {/* =====================================
                        ACTIVE CARD INDICATOR
                        ===================================== */}

                  {isPlaying && (
                    <div
                      className="playing-badge"
                      aria-label="Currently playing"
                    >
                      <span className="equalizer">
                        <i />
                        <i />
                        <i />
                        <i />
                      </span>
                      PLAYING
                    </div>
                  )}

                  {/* =====================================
                        ALBUM ART
                        ===================================== */}

                  <div className={`cover cover-${(index % 8) + 1}`}>
                    <div className="cover-noise" />

                    <div className="cover-number">
                      {String(index + 1).padStart(2, "0")}
                    </div>

                    <div className="music-symbol">♫</div>

                    <div className="cover-glow" />

                    <div className="cover-rings">
                      <span />
                      <span />
                      <span />
                    </div>

                    <div className="cover-play-overlay">
                      <button
                        type="button"
                        onClick={() => playSong(song)}
                        aria-label={`Play ${song.title}`}
                      >
                        {isPlaying ? "Ⅱ" : "▶"}
                      </button>
                    </div>
                  </div>

                  {/* =====================================
                        SONG INFORMATION
                        ===================================== */}

                  <div className="song-info">
                    <div className="song-title-row">
                      <h3 title={song.title}>{song.title}</h3>

                      {isLiked && (
                        <span
                          className="liked-icon"
                          title="Liked"
                          aria-label="Liked"
                        >
                          ♥
                        </span>
                      )}
                    </div>

                    <p className="artist" title={song.artist}>
                      {song.artist}
                    </p>

                    <div className="song-meta">
                      <span className="genre">{song.genre}</span>

                      <span className="meta-dot">•</span>

                      <span className="year">{song.release_year || "—"}</span>

                      <span className="meta-dot">•</span>

                      <span className="song-id">ID #{song.id}</span>
                    </div>

                    {/* =================================
                          POPULARITY
                          ================================= */}

                    <div className="popularity">
                      <div className="popularity-top">
                        <span>POPULARITY</span>

                        <strong>{popularity}</strong>
                      </div>

                      <div className="popularity-bar">
                        <div
                          className="popularity-fill"
                          style={{
                            width: `${popularity}%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* =================================
                          ACTIONS
                          ================================= */}

                    <div className="actions">
                      <button
                        className={`play-button ${isPlaying ? "playing" : ""}`}
                        onClick={() => playSong(song)}
                        type="button"
                      >
                        <span>{isPlaying ? "♫" : "▶"}</span>

                        {isPlaying ? "Playing" : "Play"}
                      </button>

                      <button
                        className={`like-button ${isLiked ? "liked" : ""}`}
                        onClick={() => likeSong(song)}
                        disabled={likingId === song.id}
                        type="button"
                      >
                        <span>{likingId === song.id ? "..." : "♥"}</span>

                        {likingId === song.id
                          ? "Saving"
                          : isLiked
                            ? "Liked"
                            : "Like"}
                      </button>

                      <button
                        className="playlist-button"
                        onClick={() => addSongToPlaylist(song)}
                        type="button"
                      >
                        + Playlist
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </main>

      {/* =================================================
          FLOATING NOW PLAYING PLAYER
          ================================================= */}

      {selected && (
        <div className="player" role="region" aria-label="Music player">
          {/* =============================================
              PLAYER HEADER
              ============================================= */}

          <div className="player-top">
            <div className="player-info">
              <div
                className={`mini-cover ${
                  activeSongIndex >= 0
                    ? `cover-${(activeSongIndex % 8) + 1}`
                    : ""
                }`}
              >
                <span>♫</span>

                <div className="mini-equalizer">
                  <i />
                  <i />
                  <i />
                </div>
              </div>

              <div className="player-song">
                <span className="now-playing-label">NOW PLAYING</span>

                <strong title={selected.title}>{selected.title}</strong>

                <span title={selected.artist}>{selected.artist}</span>
              </div>
            </div>

            <div className="player-meta">
              <span>{selected.genre}</span>

              <span>•</span>

              <span>{selected.release_year}</span>
            </div>
          </div>

          {/* =============================================
              PLAYER CONTROLS
              ============================================= */}

          <div className="player-controls">
            <button
              type="button"
              className="player-control"
              onClick={playPreviousSong}
              aria-label="Previous song"
              title="Previous"
            >
              ‹‹
            </button>

            <button
              type="button"
              className="player-main-button"
              onClick={toggleYouTubePlayback}
              aria-label={youtubePlaying ? "Pause current song" : "Play current song"}
            >
              {youtubePlaying ? "Ⅱ" : "▶"}
            </button>

            <button
              type="button"
              className="player-control"
              onClick={playNextSong}
              aria-label="Next song"
              title="Next"
            >
              ››
            </button>
          </div>

          {/* =============================================
              PLAYER CONTENT
              ============================================= */}

          <div className="player-content">
            {selected.youtube_video_id ? (
              <div
                ref={youtubeContainerRef}
                className="youtube-player"
              />
            ) : (
              <div className="placeholder">
                <div className="placeholder-icon">♪</div>

                <div>
                  <strong>Ready to play</strong>

                  <p>
                    This demo song doesn't have a verified YouTube video ID yet.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* =============================================
              PLAYER FOOTER
              ============================================= */}

          <div className="player-footer">
            <div className="player-progress">
              <span
                style={{
                  width: `${youtubeProgress}%`,
                }}
              />
            </div>

            <div className="player-footer-info">
              <span>
                {activeSongIndex >= 0
                  ? `Track ${activeSongIndex + 1} of ${songs.length}`
                  : "Mini Spotify"}
              </span>

              <span>♫ Playing</span>
            </div>
          </div>

          {/* =============================================
              CLOSE
              ============================================= */}

          <button
            className="close-player"
            onClick={closePlayer}
            aria-label="Close music player"
            title="Close player"
            type="button"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
