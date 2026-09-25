-- =====================================================
-- MINI SPOTIFY DATA WAREHOUSE
-- STAR SCHEMA
-- =====================================================

-- -------------------------
-- USER DIMENSION
-- -------------------------
CREATE TABLE IF NOT EXISTS dim_user (
    user_key BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    user_name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP
);


-- -------------------------
-- ARTIST DIMENSION
-- -------------------------
CREATE TABLE IF NOT EXISTS dim_artist (
    artist_key BIGSERIAL PRIMARY KEY,
    source_artist_id BIGINT,
    artist_name VARCHAR(255) NOT NULL
);


-- -------------------------
-- GENRE DIMENSION
-- -------------------------
CREATE TABLE IF NOT EXISTS dim_genre (
    genre_key BIGSERIAL PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL UNIQUE
);


-- -------------------------
-- DATE DIMENSION
-- -------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    day INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    quarter INTEGER,
    year INTEGER
);


-- -------------------------
-- SONG DIMENSION
-- -------------------------
CREATE TABLE IF NOT EXISTS dim_song (
    song_key BIGSERIAL PRIMARY KEY,

    source_track_id BIGINT UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,

    artist_key BIGINT,
    genre_key BIGINT,

    album_id BIGINT,
    album_title VARCHAR(500),

    duration_seconds NUMERIC(10,2),
    fma_listens BIGINT,
    fma_favorites BIGINT,
    fma_interest BIGINT,

    FOREIGN KEY (artist_key)
        REFERENCES dim_artist(artist_key),

    FOREIGN KEY (genre_key)
        REFERENCES dim_genre(genre_key)
);


-- -------------------------
-- LISTENING FACT TABLE
-- -------------------------
CREATE TABLE IF NOT EXISTS fact_listening (
    listening_key BIGSERIAL PRIMARY KEY,

    user_key BIGINT NOT NULL,
    song_key BIGINT NOT NULL,
    artist_key BIGINT,
    genre_key BIGINT,
    date_key INTEGER NOT NULL,

    started_at TIMESTAMP NOT NULL,

    duration_played NUMERIC(10,2) DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    liked BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (user_key)
        REFERENCES dim_user(user_key),

    FOREIGN KEY (song_key)
        REFERENCES dim_song(song_key),

    FOREIGN KEY (artist_key)
        REFERENCES dim_artist(artist_key),

    FOREIGN KEY (genre_key)
        REFERENCES dim_genre(genre_key),

    FOREIGN KEY (date_key)
        REFERENCES dim_date(date_key)
);