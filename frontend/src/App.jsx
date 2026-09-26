import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const PAGE_SIZE = 30;
const MAX_LIBRARY_LIMIT = 100;
const PLAYLIST_ENDPOINT = `${API}/api/playlists`;

const adminStats = {
  users: 1248,
  songs: 106573,
  plays: 24891,
  likes: 8426,
};

const topSongs = [
  ["Demo Pop One", "Demo Artist A", "3,842"],
  ["Demo Pop Two", "Demo Artist B", "3,421"],
  ["Demo Rock One", "Demo Artist C", "2,987"],
  ["Demo Rock Two", "Demo Artist D", "2,614"],
  ["Demo Hip Hop One", "Demo Artist E", "2,105"],
];

const topArtists = [
  ["Demo Artist A", "8,420"],
  ["Demo Artist B", "7,914"],
  ["Demo Artist C", "6,842"],
  ["Demo Artist D", "5,931"],
  ["Demo Artist E", "4,816"],
];

const genres = [
  ["Pop", 34],
  ["Rock", 24],
  ["Hip-Hop", 18],
  ["Indie", 12],
  ["Electronic", 7],
  ["Other", 5],
];

const trends = [
  ["Mon", 42],
  ["Tue", 58],
  ["Wed", 51],
  ["Thu", 72],
  ["Fri", 84],
  ["Sat", 96],
  ["Sun", 68],
];

function App() {
  const [songs, setSongs] = useState([]);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(null);

  const [token, setToken] = useState(localStorage.getItem("token") || "");

  const [likedSongs, setLikedSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loggingIn, setLoggingIn] = useState(false);
  const [likingId, setLikingId] = useState(null);

  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);

  const [showDashboard, setShowDashboard] = useState(false);
  const [showStats, setShowStats] = useState(false);

  const [libraryLimit, setLibraryLimit] = useState(PAGE_SIZE);
  const [hasMoreSongs, setHasMoreSongs] = useState(true);

  const [playlists, setPlaylists] = useState([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState(null);
  const [loadingPlaylists, setLoadingPlaylists] = useState(false);
  const [playlistError, setPlaylistError] = useState("");
  const [playlistStatus, setPlaylistStatus] = useState("");

  const [playlistSong, setPlaylistSong] = useState(null);
  const [showPlaylistModal, setShowPlaylistModal] = useState(false);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState("");
  const [addingToPlaylist, setAddingToPlaylist] = useState(false);
  const [removingFromPlaylist, setRemovingFromPlaylist] = useState(null);

  const searchRef = useRef(null);

  const totalSongs = songs.length;
  const totalLiked = likedSongs.length;

  const genreCount = useMemo(
    () => new Set(songs.map((s) => s.genre).filter(Boolean)).size,
    [songs],
  );

  const averagePopularity = useMemo(() => {
    if (!songs.length) return 0;
    return Math.round(
      songs.reduce(
        (sum, s) => sum + Math.min(Math.max(Number(s.popularity) || 0, 0), 100),
        0,
      ) / songs.length,
    );
  }, [songs]);

  const activeIndex = selected
    ? songs.findIndex((song) => song.id === selected.id)
    : -1;

  /* -----------------------------------------------------
     SONGS
     ----------------------------------------------------- */

  async function loadSongs(search = "", limit = PAGE_SIZE) {
    try {
      setLoading(true);
      setError("");

      const clean = search.trim();

      if (clean) {
        const res = await axios.get(
          `${API}/api/songs/search?q=${encodeURIComponent(clean)}`,
        );

        setSongs(Array.isArray(res.data) ? res.data : []);
        setHasMoreSongs(false);
      } else {
        const res = await axios.get(`${API}/api/songs`, {
          params: { limit },
        });

        const data = Array.isArray(res.data) ? res.data : [];

        setSongs(data);
        setLibraryLimit(limit);

        setHasMoreSongs(data.length >= limit && limit < MAX_LIBRARY_LIMIT);
      }
    } catch (err) {
      console.error(err);
      setSongs([]);
      setHasMoreSongs(false);
      setError(
        "Unable to load songs. Please make sure the backend is running.",
      );
    } finally {
      setLoading(false);
      setSearching(false);
    }
  }

  async function loadMoreSongs() {
    if (loadingMore || q.trim()) return;

    try {
      setLoadingMore(true);
      setError("");

      const nextLimit = Math.min(libraryLimit + PAGE_SIZE, MAX_LIBRARY_LIMIT);

      const res = await axios.get(`${API}/api/songs`, {
        params: { limit: nextLimit },
      });

      const data = Array.isArray(res.data) ? res.data : [];
      const previousCount = songs.length;

      setSongs(data);
      setLibraryLimit(nextLimit);

      const increased = data.length > previousCount;
      const apiMayHaveMore =
        data.length >= nextLimit && nextLimit < MAX_LIBRARY_LIMIT;

      setHasMoreSongs(apiMayHaveMore);

      if (!increased) {
        setHasMoreSongs(false);
        setStatus(`All ${data.length} currently available songs are loaded.`);
      } else {
        setStatus(`Loaded ${data.length} songs.`);
      }
    } catch (err) {
      console.error(err);
      setError("Unable to load more songs. Please try again.");
    } finally {
      setLoadingMore(false);
    }
  }

  useEffect(() => {
    loadSongs();
  }, []);

  /* -----------------------------------------------------
     KEYBOARD / FEEDBACK
     ----------------------------------------------------- */

  useEffect(() => {
    if (!status && !playlistStatus) return;

    const timer = setTimeout(() => {
      setStatus("");
      setPlaylistStatus("");
    }, 3500);

    return () => clearTimeout(timer);
  }, [status, playlistStatus]);

  useEffect(() => {
    function onKeyDown(e) {
      const tag = e.target?.tagName?.toLowerCase();
      const typing =
        tag === "input" || tag === "textarea" || e.target?.isContentEditable;

      if (e.key === "/" && !typing) {
        e.preventDefault();
        searchRef.current?.focus();
      }

      if (e.key === "Escape") {
        if (showPlaylistModal) closePlaylistModal();
        else setSelected(null);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [showPlaylistModal]);

  /* -----------------------------------------------------
     AUTH / LIKES / HISTORY
     ----------------------------------------------------- */

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
      console.error(err);
      setStatus("Login failed. Please check the backend.");
    } finally {
      setLoggingIn(false);
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setToken("");
    setLikedSongs([]);
    setSelected(null);
    setStatus("Signed out.");
  }

  async function likeSong(song) {
    if (!token) {
      setStatus("Please click Demo Login first.");
      return;
    }

    if (likedSongs.includes(song.id)) {
      setStatus(`"${song.title}" is already liked.`);
      return;
    }

    try {
      setLikingId(song.id);

      await axios.post(
        `${API}/api/songs/${song.id}/like`,
        {},
        { headers: { Authorization: `Bearer ${token}` } },
      );

      setLikedSongs((prev) => [...prev, song.id]);
      setStatus(`♥ Added "${song.title}" to your likes.`);
    } catch (err) {
      console.error(err);
      setStatus("Unable to like this song.");
    } finally {
      setLikingId(null);
    }
  }

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
        { headers: { Authorization: `Bearer ${token}` } },
      );
    } catch (err) {
      console.error("History error:", err);
    }
  }

  function playSong(song) {
    setSelected(song);
    recordPlay(song);
    setStatus(`▶ Now playing "${song.title}"`);
  }

  function playNext() {
    if (!songs.length) return;
    const index = activeIndex >= 0 ? (activeIndex + 1) % songs.length : 0;
    playSong(songs[index]);
  }

  function playPrevious() {
    if (!songs.length) return;
    const index = activeIndex > 0 ? activeIndex - 1 : songs.length - 1;
    playSong(songs[index]);
  }

  /* -----------------------------------------------------
     SEARCH
     ----------------------------------------------------- */

  function searchSongs() {
    setSearching(true);
    setLibraryLimit(PAGE_SIZE);
    loadSongs(q, PAGE_SIZE);
  }

  function clearSearch() {
    setQ("");
    setError("");
    setLibraryLimit(PAGE_SIZE);
    setHasMoreSongs(true);
    loadSongs("", PAGE_SIZE);
    searchRef.current?.focus();
  }

  /* -----------------------------------------------------
     PLAYLISTS
     ----------------------------------------------------- */

  useEffect(() => {
    if (token) {
      loadPlaylists();
    } else {
      setPlaylists([]);
      setSelectedPlaylist(null);
    }
  }, [token]);

  async function loadPlaylists() {
    if (!token) {
      setPlaylistError("Please login first to view playlists.");
      return;
    }

    try {
      setLoadingPlaylists(true);
      setPlaylistError("");

      const res = await axios.get(PLAYLIST_ENDPOINT, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const data = Array.isArray(res.data)
        ? res.data
        : Array.isArray(res.data?.playlists)
          ? res.data.playlists
          : [];

      setPlaylists(data);

      if (data.length && !selectedPlaylist) {
        setSelectedPlaylist(data[0]);
      }
    } catch (err) {
      console.error(err);
      setPlaylists([]);

      setPlaylistError(
        err.response?.status === 404
          ? "Playlist API is not available in the current backend."
          : "Unable to load playlists.",
      );
    } finally {
      setLoadingPlaylists(false);
    }
  }

  async function openPlaylistModal(song) {
    setPlaylistSong(song);
    setSelectedPlaylistId("");
    setPlaylistError("");
    setPlaylistStatus("");
    setShowPlaylistModal(true);
    await loadPlaylists();
  }

  function closePlaylistModal() {
    if (addingToPlaylist) return;
    setShowPlaylistModal(false);
    setPlaylistSong(null);
    setSelectedPlaylistId("");
    setPlaylistError("");
  }

  async function addToPlaylist() {
    if (!playlistSong) return;

    if (!token) {
      setPlaylistError("Please login first.");
      return;
    }

    if (!selectedPlaylistId) {
      setPlaylistError("Select a playlist first.");
      return;
    }

    try {
      setAddingToPlaylist(true);
      setPlaylistError("");

      await axios.post(
        `${PLAYLIST_ENDPOINT}/${selectedPlaylistId}/songs`,
        { song_id: playlistSong.id },
        { headers: { Authorization: `Bearer ${token}` } },
      );

      setPlaylistStatus(`✓ "${playlistSong.title}" added to the playlist.`);

      setTimeout(closePlaylistModal, 700);
    } catch (err) {
      console.error(err);
      setPlaylistError(
        err.response?.status === 404
          ? "Playlist API is not available in the current backend."
          : "Unable to add this song to the playlist.",
      );
    } finally {
      setAddingToPlaylist(false);
    }
  }

  async function removeFromPlaylist(song) {
    if (!selectedPlaylist?.id) return;

    try {
      setRemovingFromPlaylist(song.id);

      await axios.delete(
        `${PLAYLIST_ENDPOINT}/${selectedPlaylist.id}/songs/${song.id}`,
        { headers: { Authorization: `Bearer ${token}` } },
      );

      setSelectedPlaylist((prev) => {
        if (!prev) return prev;

        const current = Array.isArray(prev.songs) ? prev.songs : [];

        return {
          ...prev,
          songs: current.filter((item) => item.id !== song.id),
        };
      });

      setPlaylistStatus(`"${song.title}" removed from playlist.`);
    } catch (err) {
      console.error(err);
      setPlaylistError("Unable to remove this song.");
    } finally {
      setRemovingFromPlaylist(null);
    }
  }

  const playlistSongs = Array.isArray(selectedPlaylist?.songs)
    ? selectedPlaylist.songs
    : [];

  /* -----------------------------------------------------
     RENDER
     ----------------------------------------------------- */

  return (
    <div className="page">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="ambient ambient-three" />

      {/* HEADER */}
      <header className="site-header">
        <div className="brand">
          <div className="brand-icon">♫</div>

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
            className={`admin-button ${showDashboard ? "admin-active" : ""}`}
            type="button"
            onClick={() => setShowDashboard((v) => !v)}
            aria-label={showDashboard ? "Open music library" : "Open dashboard"}
          >
            <span>{showDashboard ? "♫" : "◈"}</span>
            {showDashboard ? "Music" : "Dashboard"}
          </button>

          <button
            className="shortcut-hint"
            type="button"
            onClick={() => searchRef.current?.focus()}
            title="Focus search"
          >
            ⌕ <kbd>/</kbd>
          </button>

          <button
            className={`login-button ${token ? "logged-in" : ""}`}
            onClick={token ? logout : loginDemo}
            disabled={loggingIn}
          >
            <span className="login-dot" />
            {loggingIn ? "Signing In..." : token ? "✓ Logged In" : "Demo Login"}
          </button>
        </div>
      </header>

      {/* ADMIN DASHBOARD */}
      {showDashboard && (
        <section className="admin-dashboard">
          <div className="admin-dashboard-header">
            <div>
              <div className="section-kicker">
                <span className="kicker-line" />
                ADMIN ANALYTICS
              </div>

              <h2>
                Music <span>Dashboard</span>
              </h2>

              <p>Platform overview and listening analytics.</p>
            </div>

            <button
              className="admin-close-button"
              onClick={() => setShowDashboard(false)}
              type="button"
            >
              × Close
            </button>
          </div>

          <div className="admin-placeholder-note">
            <span>◈</span>
            <div>
              <strong>Frontend Analytics Preview</strong>
              <p>
                Preview values are placeholders until analytics APIs are
                available.
              </p>
            </div>
          </div>

          <div className="admin-stat-grid">
            {[
              ["👥", "TOTAL USERS", adminStats.users, "Registered accounts"],
              ["♪", "TOTAL SONGS", adminStats.songs, "Music library"],
              ["▶", "TOTAL PLAYS", adminStats.plays, "Recorded plays"],
              ["♥", "TOTAL LIKES", adminStats.likes, "Song likes"],
            ].map(([icon, label, value, sub]) => (
              <div className="admin-stat-card" key={label}>
                <span className="admin-stat-icon">{icon}</span>
                <div>
                  <span>{label}</span>
                  <strong>{value.toLocaleString()}</strong>
                  <small>{sub}</small>
                </div>
              </div>
            ))}
          </div>

          <div className="admin-content-grid">
            <div className="admin-panel">
              <div className="admin-panel-header">
                <div>
                  <span>MOST PLAYED</span>
                  <h3>Top Songs</h3>
                </div>
                <span className="admin-panel-badge">5 TRACKS</span>
              </div>

              <div className="admin-ranking-list">
                {topSongs.map(([title, artist, plays], i) => (
                  <div className="admin-ranking-row" key={title}>
                    <div className="ranking-number">
                      {String(i + 1).padStart(2, "0")}
                    </div>
                    <div className="ranking-info">
                      <strong>{title}</strong>
                      <span>{artist}</span>
                    </div>
                    <strong className="ranking-value">{plays}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="admin-panel">
              <div className="admin-panel-header">
                <div>
                  <span>LISTENING ACTIVITY</span>
                  <h3>Top Artists</h3>
                </div>
                <span className="admin-panel-badge">5 ARTISTS</span>
              </div>

              <div className="admin-ranking-list">
                {topArtists.map(([artist, plays]) => (
                  <div className="admin-ranking-row" key={artist}>
                    <div className="artist-avatar">{artist[0]}</div>
                    <div className="ranking-info">
                      <strong>{artist}</strong>
                      <span>Total listening activity</span>
                    </div>
                    <strong className="ranking-value">{plays}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="admin-panel">
              <div className="admin-panel-header">
                <div>
                  <span>LIBRARY MIX</span>
                  <h3>Genre Distribution</h3>
                </div>
              </div>

              <div className="genre-chart">
                {genres.map(([name, value]) => (
                  <div className="genre-row" key={name}>
                    <div className="genre-row-top">
                      <span>{name}</span>
                      <strong>{value}%</strong>
                    </div>
                    <div className="genre-bar">
                      <div
                        className="genre-fill"
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="admin-panel">
              <div className="admin-panel-header">
                <div>
                  <span>LAST 7 DAYS</span>
                  <h3>Listening Trends</h3>
                </div>
                <span className="trend-value">+18.4%</span>
              </div>

              <div className="trend-chart">
                {trends.map(([day, value]) => (
                  <div className="trend-column" key={day}>
                    <div className="trend-value-label">{value}</div>
                    <div className="trend-bar-wrapper">
                      <div
                        className="trend-bar"
                        style={{ height: `${value}%` }}
                      />
                    </div>
                    <span>{day}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {!showDashboard && (
        <>
          {/* PLAYLISTS */}
          <section className="playlist-section">
            <div className="playlist-section-header">
              <div>
                <div className="section-kicker">
                  <span className="kicker-line" />
                  YOUR COLLECTION
                </div>
                <h2>Playlists</h2>
                <p>Organize your favorite songs into collections.</p>
              </div>

              <button
                className="playlist-refresh-button"
                type="button"
                onClick={loadPlaylists}
                disabled={loadingPlaylists}
              >
                {loadingPlaylists ? "Loading..." : "↻ Refresh"}
              </button>
            </div>

            {playlistError && (
              <div className="playlist-error">
                <span>⚠</span>
                <div>
                  <strong>Playlist service unavailable</strong>
                  <p>{playlistError}</p>
                </div>
              </div>
            )}

            {playlistStatus && (
              <div className="playlist-success">
                <span>✓</span>
                {playlistStatus}
              </div>
            )}

            {loadingPlaylists ? (
              <div className="playlist-loading">
                <span className="load-more-spinner" />
                Loading playlists...
              </div>
            ) : playlists.length === 0 ? (
              <div className="playlist-empty">
                <div className="playlist-empty-icon">♫</div>
                <h3>No playlists available</h3>
                <p>
                  Your actual playlists will appear here when the playlist API
                  is available.
                </p>
              </div>
            ) : (
              <div className="playlist-layout">
                <aside className="playlist-sidebar">
                  {playlists.map((playlist) => (
                    <button
                      type="button"
                      key={playlist.id}
                      className={`playlist-item ${
                        selectedPlaylist?.id === playlist.id
                          ? "playlist-item-active"
                          : ""
                      }`}
                      onClick={() => setSelectedPlaylist(playlist)}
                    >
                      <span className="playlist-item-icon">♫</span>
                      <span className="playlist-item-copy">
                        <strong>{playlist.name}</strong>
                        <small>
                          {Array.isArray(playlist.songs)
                            ? playlist.songs.length
                            : (playlist.song_count ?? 0)}{" "}
                          songs
                        </small>
                      </span>
                    </button>
                  ))}
                </aside>

                <div className="playlist-content">
                  {selectedPlaylist && (
                    <>
                      <div className="playlist-content-header">
                        <span>SELECTED PLAYLIST</span>
                        <h3>{selectedPlaylist.name}</h3>
                      </div>

                      {playlistSongs.length === 0 ? (
                        <div className="playlist-empty playlist-empty-small">
                          <div className="playlist-empty-icon">♫</div>
                          <h3>This playlist is empty</h3>
                          <p>Add songs from your library to get started.</p>
                        </div>
                      ) : (
                        <div className="playlist-song-list">
                          {playlistSongs.map((song, i) => (
                            <div className="playlist-song-row" key={song.id}>
                              <span className="playlist-song-number">
                                {String(i + 1).padStart(2, "0")}
                              </span>
                              <div className="playlist-song-art">♫</div>
                              <div className="playlist-song-info">
                                <strong>{song.title}</strong>
                                <span>{song.artist}</span>
                              </div>
                              <button
                                className="playlist-remove-button"
                                type="button"
                                disabled={removingFromPlaylist === song.id}
                                onClick={() => removeFromPlaylist(song)}
                              >
                                {removingFromPlaylist === song.id
                                  ? "Removing..."
                                  : "Remove"}
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </section>

          {/* LIBRARY HERO */}
          <section className="library-hero">
            <div className="hero-copy">
              <div className="section-kicker">
                <span className="kicker-line" />
                YOUR MUSIC LIBRARY
              </div>

              <h2>
                Discover<span> Music</span>
              </h2>

              <p>
                Explore your collection, discover something new, and keep your
                favorites organized.
              </p>
            </div>

            <div className="library-stats">
              <button
                className={`stat-card ${showStats ? "stat-active" : ""}`}
                type="button"
                onClick={() => setShowStats((v) => !v)}
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
                <span className="stat-value">{genreCount}</span>
                <span className="stat-label">Genres</span>
              </div>
            </div>
          </section>

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
                <strong>{genreCount}</strong>
              </div>
              <div className="stats-panel-item">
                <span>Session</span>
                <strong>{token ? "Authenticated" : "Guest"}</strong>
              </div>
            </section>
          )}

          {/* SEARCH */}
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
                  type="button"
                  onClick={clearSearch}
                >
                  Clear search
                </button>
              )}
            </div>

            <div className="search">
              <span className="search-icon">⌕</span>

              <input
                ref={searchRef}
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") searchSongs();
                  if (e.key === "Escape") e.target.blur();
                }}
                placeholder="Search songs, artists or genres..."
                aria-label="Search songs"
              />

              {q && (
                <button
                  className="clear-button"
                  type="button"
                  onClick={clearSearch}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}

              <button
                className="search-button"
                type="button"
                onClick={searchSongs}
                disabled={searching}
              >
                {searching ? "Searching..." : "Search"}
              </button>
            </div>
          </section>

          {status && (
            <div className="status" role="status">
              <span className="status-pulse">●</span>
              <span>{status}</span>
              <button type="button" onClick={() => setStatus("")}>
                ×
              </button>
            </div>
          )}

          {error && (
            <div className="error-message" role="alert">
              <span>⚠</span>
              <div>
                <strong>Something went wrong</strong>
                <p>{error}</p>
              </div>
              <button type="button" onClick={() => loadSongs(q, PAGE_SIZE)}>
                Retry
              </button>
            </div>
          )}

          {/* SONG LIBRARY */}
          <main>
            {loading ? (
              <div className="loading">
                <div className="loading-orb">
                  <div className="spinner" />
                </div>
                <h3>Loading your music</h3>
                <p>Preparing your library...</p>
              </div>
            ) : songs.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">♫</div>
                <span className="section-kicker">NO RESULTS</span>
                <h2>Nothing found</h2>
                <p>We couldn't find anything matching your search.</p>
                <button type="button" onClick={clearSearch}>
                  <span>↻</span>
                  Show All Songs
                </button>
              </div>
            ) : (
              <>
                <div className="grid">
                  {songs.map((song, index) => {
                    const liked = likedSongs.includes(song.id);
                    const playing = selected?.id === song.id;
                    const popularity = Math.min(
                      Math.max(Number(song.popularity) || 0, 0),
                      100,
                    );

                    return (
                      <article
                        className={`card ${
                          playing ? "active-card" : ""
                        } ${liked ? "liked-card" : ""}`}
                        key={song.id}
                      >
                        {playing && (
                          <div className="playing-badge">
                            <span className="equalizer">
                              <i />
                              <i />
                              <i />
                              <i />
                            </span>
                            PLAYING
                          </div>
                        )}

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
                              {playing ? "Ⅱ" : "▶"}
                            </button>
                          </div>
                        </div>

                        <div className="song-info">
                          <div className="song-title-row">
                            <h3 title={song.title}>{song.title}</h3>
                            {liked && (
                              <span className="liked-icon" title="Liked">
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
                            <span className="year">{song.release_year}</span>
                          </div>

                          <div className="popularity">
                            <div className="popularity-top">
                              <span>POPULARITY</span>
                              <strong>{popularity}</strong>
                            </div>
                            <div className="popularity-bar">
                              <div
                                className="popularity-fill"
                                style={{ width: `${popularity}%` }}
                              />
                            </div>
                          </div>

                          <div className="actions">
                            <button
                              className={`play-button ${
                                playing ? "playing" : ""
                              }`}
                              type="button"
                              onClick={() => playSong(song)}
                            >
                              <span>{playing ? "♫" : "▶"}</span>
                              {playing ? "Playing" : "Play"}
                            </button>

                            <button
                              className={`like-button ${liked ? "liked" : ""}`}
                              type="button"
                              disabled={likingId === song.id}
                              onClick={() => likeSong(song)}
                            >
                              <span>{likingId === song.id ? "..." : "♥"}</span>
                              {likingId === song.id
                                ? "Saving"
                                : liked
                                  ? "Liked"
                                  : "Like"}
                            </button>

                            <button
                              className="playlist-button"
                              type="button"
                              onClick={() => openPlaylistModal(song)}
                            >
                              <span>+</span>
                              Playlist
                            </button>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>

                {!q.trim() && (
                  <div className="load-more-section">
                    {hasMoreSongs ? (
                      <button
                        className="load-more-button"
                        type="button"
                        onClick={loadMoreSongs}
                        disabled={loadingMore}
                      >
                        {loadingMore ? (
                          <>
                            <span className="load-more-spinner" />
                            Loading more songs...
                          </>
                        ) : (
                          <>
                            <span>↓</span>
                            Load More Songs
                          </>
                        )}
                      </button>
                    ) : (
                      <button
                        className="load-more-button"
                        type="button"
                        disabled
                        aria-disabled="true"
                        title="The API returned all currently available songs"
                      >
                        <span>✓</span>
                        All available songs loaded
                      </button>
                    )}
                  </div>
                )}
              </>
            )}
          </main>

          {/* PLAYLIST MODAL */}
          {showPlaylistModal && playlistSong && (
            <div
              className="playlist-modal-backdrop"
              onMouseDown={(e) => {
                if (e.target === e.currentTarget) closePlaylistModal();
              }}
            >
              <div
                className="playlist-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="playlist-modal-title"
              >
                <div className="playlist-modal-header">
                  <div>
                    <span>ADD TO PLAYLIST</span>
                    <h2 id="playlist-modal-title">Choose a playlist</h2>
                    <p>{playlistSong.title}</p>
                  </div>

                  <button
                    className="playlist-modal-close"
                    type="button"
                    onClick={closePlaylistModal}
                    disabled={addingToPlaylist}
                    aria-label="Close"
                  >
                    ×
                  </button>
                </div>

                {loadingPlaylists ? (
                  <div className="playlist-modal-loading">
                    <span className="load-more-spinner" />
                    Loading your playlists...
                  </div>
                ) : playlists.length === 0 ? (
                  <div className="playlist-modal-empty">
                    <div>♫</div>
                    <h3>No playlists found</h3>
                    <p>
                      {playlistError ||
                        "No playlists are available for this account."}
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="playlist-select-list">
                      {playlists.map((playlist) => (
                        <button
                          type="button"
                          key={playlist.id}
                          className={`playlist-select-option ${
                            selectedPlaylistId === String(playlist.id)
                              ? "selected"
                              : ""
                          }`}
                          onClick={() =>
                            setSelectedPlaylistId(String(playlist.id))
                          }
                        >
                          <span className="playlist-option-icon">♫</span>

                          <span>
                            <strong>{playlist.name}</strong>
                            <small>
                              {Array.isArray(playlist.songs)
                                ? playlist.songs.length
                                : (playlist.song_count ?? 0)}{" "}
                              songs
                            </small>
                          </span>

                          <span className="playlist-option-check">
                            {selectedPlaylistId === String(playlist.id)
                              ? "✓"
                              : ""}
                          </span>
                        </button>
                      ))}
                    </div>

                    {playlistError && (
                      <div className="playlist-modal-error">
                        ⚠ {playlistError}
                      </div>
                    )}

                    {playlistStatus && (
                      <div className="playlist-modal-success">
                        ✓ {playlistStatus}
                      </div>
                    )}

                    <div className="playlist-modal-actions">
                      <button
                        className="playlist-cancel-button"
                        type="button"
                        onClick={closePlaylistModal}
                        disabled={addingToPlaylist}
                      >
                        Cancel
                      </button>

                      <button
                        className="playlist-add-button"
                        type="button"
                        onClick={addToPlaylist}
                        disabled={addingToPlaylist || !selectedPlaylistId}
                      >
                        {addingToPlaylist ? "Adding..." : "Add to Playlist"}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* PLAYER */}
      {selected && (
        <div className="player" role="region" aria-label="Music player">
          <div className="player-top">
            <div className="player-info">
              <div
                className={`mini-cover ${
                  activeIndex >= 0 ? `cover-${(activeIndex % 8) + 1}` : ""
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

          <div className="player-controls">
            <button
              className="player-control"
              type="button"
              onClick={playPrevious}
              aria-label="Previous song"
            >
              ‹‹
            </button>

            <button
              className="player-main-button"
              type="button"
              onClick={() => playSong(selected)}
              aria-label="Play current song"
            >
              ▶
            </button>

            <button
              className="player-control"
              type="button"
              onClick={playNext}
              aria-label="Next song"
            >
              ››
            </button>
          </div>

          <div className="player-content">
            {selected.youtube_video_id ? (
              <iframe
                src={`https://www.youtube.com/embed/${selected.youtube_video_id}`}
                title={`Playing ${selected.title}`}
                allow="autoplay; encrypted-media; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="placeholder">
                <div className="placeholder-icon">♪</div>
                <div>
                  <strong>Ready to play</strong>
                  <p>This song doesn't have a verified YouTube video ID.</p>
                </div>
              </div>
            )}
          </div>

          <div className="player-footer">
            <div className="player-progress">
              <span />
            </div>

            <div className="player-footer-info">
              <span>
                {activeIndex >= 0
                  ? `Track ${activeIndex + 1} of ${songs.length}`
                  : "Mini Spotify"}
              </span>
              <span>♫ Playing</span>
            </div>
          </div>

          <button
            className="close-player"
            type="button"
            onClick={() => setSelected(null)}
            aria-label="Close player"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
