-- =====================================================
-- MINI SPOTIFY OLAP QUERIES
-- =====================================================


-- 1. MOST PLAYED SONGS
SELECT
    s.title,
    a.artist_name,
    COUNT(*) AS total_plays
FROM fact_listening f
JOIN dim_song s
    ON f.song_key = s.song_key
JOIN dim_artist a
    ON f.artist_key = a.artist_key
GROUP BY s.title, a.artist_name
ORDER BY total_plays DESC
LIMIT 10;


-- 2. MOST PLAYED ARTISTS
SELECT
    a.artist_name,
    COUNT(*) AS total_plays
FROM fact_listening f
JOIN dim_artist a
    ON f.artist_key = a.artist_key
GROUP BY a.artist_name
ORDER BY total_plays DESC
LIMIT 10;


-- 3. LISTENING BY GENRE AND MONTH
SELECT
    d.year,
    d.month,
    d.month_name,
    g.genre_name,
    COUNT(*) AS total_plays,
    SUM(f.duration_played) AS total_seconds
FROM fact_listening f
JOIN dim_date d
    ON f.date_key = d.date_key
JOIN dim_genre g
    ON f.genre_key = g.genre_key
GROUP BY
    d.year,
    d.month,
    d.month_name,
    g.genre_name
ORDER BY
    d.year,
    d.month,
    total_plays DESC;