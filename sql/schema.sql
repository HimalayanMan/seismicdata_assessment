PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS file (
    file_id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS network (
    network_id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS station (
    station_id INTEGER PRIMARY KEY,
    network_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    latitude REAL CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    longitude REAL CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    elevation_m REAL,
    site_name TEXT,
    FOREIGN KEY (network_id) REFERENCES network(network_id) ON DELETE RESTRICT,
    UNIQUE (network_id, code)
);

CREATE TABLE IF NOT EXISTS channel (
    channel_id INTEGER PRIMARY KEY,
    station_id INTEGER NOT NULL,
    location_code TEXT NOT NULL DEFAULT '',
    code TEXT NOT NULL,
    sample_rate_hz REAL CHECK (sample_rate_hz IS NULL OR sample_rate_hz > 0),
    sensor_description TEXT,
    FOREIGN KEY (station_id) REFERENCES station(station_id) ON DELETE RESTRICT,
    UNIQUE (station_id, location_code, code)
);

CREATE TABLE IF NOT EXISTS waveform_segment (
    segment_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    n_samples INTEGER NOT NULL CHECK (n_samples >= 0),
    sample_rate_hz REAL CHECK (sample_rate_hz IS NULL OR sample_rate_hz > 0),
    data_min REAL,
    data_max REAL,
    data_mean REAL,
    FOREIGN KEY (file_id) REFERENCES file(file_id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES channel(channel_id) ON DELETE RESTRICT,
    CHECK (end_time >= start_time)
);

CREATE TABLE IF NOT EXISTS sample (
    segment_id INTEGER NOT NULL,
    sample_index INTEGER NOT NULL CHECK (sample_index >= 0),
    sample_time TEXT NOT NULL,
    value REAL NOT NULL,
    FOREIGN KEY (segment_id) REFERENCES waveform_segment(segment_id) ON DELETE CASCADE,
    PRIMARY KEY (segment_id, sample_index)
);

CREATE INDEX IF NOT EXISTS idx_file_filename
    ON file(filename);

CREATE INDEX IF NOT EXISTS idx_network_code
    ON network(code);

CREATE INDEX IF NOT EXISTS idx_station_code
    ON station(code);

CREATE INDEX IF NOT EXISTS idx_station_coordinates
    ON station(latitude, longitude);

CREATE INDEX IF NOT EXISTS idx_channel_code
    ON channel(code);

CREATE INDEX IF NOT EXISTS idx_segment_time
    ON waveform_segment(start_time, end_time);

CREATE INDEX IF NOT EXISTS idx_sample_time
    ON sample(sample_time);
