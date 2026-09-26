import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function formatHours(seconds) {
  const hours = (Number(seconds) || 0) / 3600;

  if (hours < 1) {
    return `${Math.round(hours * 60)} min`;
  }

  return `${hours.toFixed(1)} hrs`;
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const response = await axios.get(
        `${API}/api/analytics/dashboard`,
      );

      setData(response.data);
    } catch (err) {
      console.error("Dashboard loading error:", err);

      setError(
        "Unable to load analytics. Make sure the backend is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const maxSongPlays = useMemo(() => {
    if (!data?.top_songs?.length) return 1;

    return Math.max(
      ...data.top_songs.map((song) => Number(song.total_plays) || 0),
    );
  }, [data]);

  const maxArtistPlays = useMemo(() => {
    if (!data?.top_artists?.length) return 1;

    return Math.max(
      ...data.top_artists.map(
        (artist) => Number(artist.total_plays) || 0,
      ),
    );
  }, [data]);

  const maxGenrePlays = useMemo(() => {
    if (!data?.genres?.length) return 1;

    return Math.max(
      ...data.genres.map(
        (genre) => Number(genre.total_plays) || 0,
      ),
    );
  }, [data]);

  const maxTrendPlays = useMemo(() => {
    if (!data?.trends?.length) return 1;

    return Math.max(
      ...data.trends.map(
        (trend) => Number(trend.total_plays) || 0,
      ),
    );
  }, [data]);

  if (loading) {
    return (
      <section className="analytics-dashboard">
        <div className="dashboard-loading">
          <div className="dashboard-spinner" />
          <h2>Loading analytics</h2>
          <p>Reading your PostgreSQL warehouse...</p>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="analytics-dashboard">
        <div className="dashboard-error">
          <div className="dashboard-error-icon">!</div>

          <h2>Analytics unavailable</h2>

          <p>{error}</p>

          <button
            type="button"
            onClick={loadDashboard}
            className="dashboard-retry"
          >
            Try Again
          </button>
        </div>
      </section>
    );
  }

  const summary = data.summary;

  return (
    <section className="analytics-dashboard">
      <div className="dashboard-heading">
        <div>
          <span className="section-kicker">
            <span className="kicker-line" />
            ADMIN ANALYTICS
          </span>

          <h2>
            Music
            <span> Intelligence</span>
          </h2>

          <p>
            Live analytics from the Mini Spotify PostgreSQL warehouse.
          </p>
        </div>

        <button
          type="button"
          className="dashboard-refresh"
          onClick={loadDashboard}
        >
          ↻ Refresh
        </button>
      </div>

      <div className="dashboard-kpis">
        <div className="dashboard-kpi">
          <span className="dashboard-kpi-icon">♟</span>
          <span className="dashboard-kpi-label">Total Users</span>
          <strong>{formatNumber(summary.total_users)}</strong>
          <small>{formatNumber(summary.active_users)} active in warehouse</small>
        </div>

        <div className="dashboard-kpi">
          <span className="dashboard-kpi-icon">♫</span>
          <span className="dashboard-kpi-label">Total Songs</span>
          <strong>{formatNumber(summary.total_songs)}</strong>
          <small>{formatNumber(summary.active_songs)} currently played</small>
        </div>

        <div className="dashboard-kpi">
          <span className="dashboard-kpi-icon">▶</span>
          <span className="dashboard-kpi-label">Total Plays</span>
          <strong>{formatNumber(summary.total_plays)}</strong>
          <small>{formatHours(summary.total_seconds)} listening time</small>
        </div>

        <div className="dashboard-kpi">
          <span className="dashboard-kpi-icon">♥</span>
          <span className="dashboard-kpi-label">Total Likes</span>
          <strong>{formatNumber(summary.total_likes)}</strong>
          <small>{formatNumber(summary.total_artists)} artists</small>
        </div>
      </div>

      <div className="dashboard-main-grid">
        <section className="dashboard-card dashboard-wide">
          <div className="dashboard-card-heading">
            <div>
              <span className="dashboard-card-kicker">OLAP ANALYSIS</span>
              <h3>Most Played Songs</h3>
            </div>

            <span className="dashboard-card-count">
              Top {data.top_songs.length}
            </span>
          </div>

          <div className="dashboard-ranking-list">
            {data.top_songs.map((song, index) => {
              const plays = Number(song.total_plays) || 0;
              const width = (plays / maxSongPlays) * 100;

              return (
                <div className="dashboard-ranking-row" key={`${song.title}-${index}`}>
                  <span className="dashboard-rank">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <div className="dashboard-ranking-content">
                    <div className="dashboard-ranking-title">
                      <strong title={song.title}>{song.title}</strong>
                      <span>{song.artist_name}</span>
                    </div>

                    <div className="dashboard-bar">
                      <div
                        className="dashboard-bar-fill"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                  </div>

                  <strong className="dashboard-ranking-value">
                    {plays}
                  </strong>
                </div>
              );
            })}
          </div>
        </section>

        <section className="dashboard-card">
          <div className="dashboard-card-heading">
            <div>
              <span className="dashboard-card-kicker">OLAP ANALYSIS</span>
              <h3>Top Artists</h3>
            </div>
          </div>

          <div className="dashboard-ranking-list">
            {data.top_artists.map((artist, index) => {
              const plays = Number(artist.total_plays) || 0;
              const width = (plays / maxArtistPlays) * 100;

              return (
                <div className="dashboard-compact-row" key={`${artist.artist_name}-${index}`}>
                  <span className="dashboard-compact-rank">
                    {index + 1}
                  </span>

                  <div className="dashboard-compact-main">
                    <div>
                      <strong title={artist.artist_name}>
                        {artist.artist_name}
                      </strong>

                      <span>{plays} plays</span>
                    </div>

                    <div className="dashboard-bar">
                      <div
                        className="dashboard-bar-fill"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="dashboard-card">
          <div className="dashboard-card-heading">
            <div>
              <span className="dashboard-card-kicker">MUSIC DIMENSION</span>
              <h3>Genre Distribution</h3>
            </div>

            <span className="dashboard-card-count">
              {data.genres.length} genres
            </span>
          </div>

          <div className="dashboard-genre-list">
            {data.genres.map((genre) => {
              const plays = Number(genre.total_plays) || 0;
              const width = (plays / maxGenrePlays) * 100;

              return (
                <div className="dashboard-genre-row" key={genre.genre_name}>
                  <div>
                    <span>{genre.genre_name}</span>
                    <strong>{plays}</strong>
                  </div>

                  <div className="dashboard-bar">
                    <div
                      className="dashboard-bar-fill"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="dashboard-card dashboard-wide">
          <div className="dashboard-card-heading">
            <div>
              <span className="dashboard-card-kicker">DATE DIMENSION</span>
              <h3>Listening Trends</h3>
            </div>

            <span className="dashboard-card-count">
              {data.trends.length} months
            </span>
          </div>

          <div className="dashboard-trend-chart">
            {data.trends.map((trend) => {
              const plays = Number(trend.total_plays) || 0;
              const height = Math.max(
                (plays / maxTrendPlays) * 100,
                5,
              );

              return (
                <div
                  className="dashboard-trend-column"
                  key={`${trend.year}-${trend.month}`}
                >
                  <div className="dashboard-trend-value">
                    {formatNumber(plays)}
                  </div>

                  <div className="dashboard-trend-track">
                    <div
                      className="dashboard-trend-fill"
                      style={{ height: `${height}%` }}
                    />
                  </div>

                  <span>
                    {trend.month_name.slice(0, 3)}
                  </span>

                  <small>{trend.year}</small>
                </div>
              );
            })}
          </div>
        </section>

        <section className="dashboard-card dashboard-wide">
          <div className="dashboard-card-heading">
            <div>
              <span className="dashboard-card-kicker">USER ANALYSIS</span>
              <h3>Listening Patterns</h3>
            </div>

            <span className="dashboard-card-count">
              Top active users
            </span>
          </div>

          <div className="dashboard-user-table-wrap">
            <table className="dashboard-user-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Plays</th>
                  <th>Listening</th>
                  <th>Unique Songs</th>
                  <th>Genres</th>
                </tr>
              </thead>

              <tbody>
                {data.users.map((user) => (
                  <tr key={user.user_id}>
                    <td>{user.user_name}</td>
                    <td>{user.total_plays}</td>
                    <td>{formatHours(user.total_seconds)}</td>
                    <td>{user.unique_songs}</td>
                    <td>{user.unique_genres}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </section>
  );
}

export default Dashboard;