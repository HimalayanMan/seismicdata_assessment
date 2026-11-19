from pathlib import Path
import sqlite3

SQL_SCHEMA = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"

def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = SQL_SCHEMA.read_text(encoding="utf-8")
    with connect(db_path) as conn:
        conn.executescript(schema)
        conn.commit()

def upsert_network(conn, code: str, description=None) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO network(code, description) VALUES (?, ?)",
        (code, description),
    )
    return conn.execute(
        "SELECT network_id FROM network WHERE code = ?", (code,)
    ).fetchone()[0]

def upsert_station(conn, network_id: int, code: str,
                   latitude=None, longitude=None,
                   elevation_m=None, site_name=None) -> int:
    conn.execute("""
        INSERT INTO station
            (network_id, code, latitude, longitude, elevation_m, site_name)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(network_id, code) DO UPDATE SET
            latitude = COALESCE(excluded.latitude, station.latitude),
            longitude = COALESCE(excluded.longitude, station.longitude),
            elevation_m = COALESCE(excluded.elevation_m, station.elevation_m),
            site_name = COALESCE(excluded.site_name, station.site_name)
    """, (network_id, code, latitude, longitude, elevation_m, site_name))

    return conn.execute("""
        SELECT station_id
        FROM station
        WHERE network_id = ? AND code = ?
    """, (network_id, code)).fetchone()[0]

def upsert_channel(conn, station_id: int, location_code: str,
                   code: str, sample_rate_hz=None,
                   sensor_description=None) -> int:
    location_code = location_code or ""
    conn.execute("""
        INSERT INTO channel
            (station_id, location_code, code,
             sample_rate_hz, sensor_description)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(station_id, location_code, code) DO UPDATE SET
            sample_rate_hz =
                COALESCE(excluded.sample_rate_hz, channel.sample_rate_hz),
            sensor_description =
                COALESCE(excluded.sensor_description,
                         channel.sensor_description)
    """, (station_id, location_code, code,
          sample_rate_hz, sensor_description))

    return conn.execute("""
        SELECT channel_id
        FROM channel
        WHERE station_id = ? AND location_code = ? AND code = ?
    """, (station_id, location_code, code)).fetchone()[0]
