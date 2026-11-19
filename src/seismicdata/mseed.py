from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import math
import sqlite3

import numpy as np
from obspy import read, UTCDateTime

from .db import upsert_channel, upsert_network, upsert_station

@dataclass
class TraceMetadata:
    source_file: str
    network: str
    station: str
    location: str
    channel: str
    start_time: str
    end_time: str
    n_samples: int
    sample_rate_hz: float
    min_value: float
    max_value: float
    mean_value: float

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def iso_time(value: UTCDateTime) -> str:
    return value.datetime.isoformat(timespec="milliseconds")

def trace_metadata(trace, source_file: Path) -> TraceMetadata:
    values = np.asarray(trace.data, dtype=np.float64)
    return TraceMetadata(
        source_file=source_file.name,
        network=str(trace.stats.get("network", "")),
        station=str(trace.stats.get("station", "")),
        location=str(trace.stats.get("location", "")),
        channel=str(trace.stats.get("channel", "")),
        start_time=iso_time(trace.stats.starttime),
        end_time=iso_time(trace.stats.endtime),
        n_samples=int(trace.stats.npts),
        sample_rate_hz=float(trace.stats.sampling_rate),
        min_value=float(np.nanmin(values)),
        max_value=float(np.nanmax(values)),
        mean_value=float(np.nanmean(values)),
    )

def ingest_file(conn: sqlite3.Connection, path: Path,
                 store_samples: bool = True) -> list[TraceMetadata]:
    stream = read(str(path))

    conn.execute("""
        INSERT OR IGNORE INTO file(path, filename, sha256)
        VALUES (?, ?, ?)
    """, (str(path.resolve()), path.name, sha256_file(path)))

    file_id = conn.execute(
        "SELECT file_id FROM file WHERE path = ?",
        (str(path.resolve()),)
    ).fetchone()[0]

    records = []

    for trace in stream:
        meta = trace_metadata(trace, path)
        records.append(meta)

        network_id = upsert_network(conn, meta.network)
        station_id = upsert_station(conn, network_id, meta.station)
        channel_id = upsert_channel(
            conn,
            station_id,
            meta.location,
            meta.channel,
            meta.sample_rate_hz,
        )

        # Make repeated pipeline execution idempotent for the same source
        # segment.
        conn.execute("""
            DELETE FROM waveform_segment
            WHERE file_id = ?
              AND channel_id = ?
              AND start_time = ?
        """, (file_id, channel_id, meta.start_time))

        cur = conn.execute("""
            INSERT INTO waveform_segment
                (file_id, channel_id, start_time, end_time, n_samples,
                 sample_rate_hz, data_min, data_max, data_mean)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id,
            channel_id,
            meta.start_time,
            meta.end_time,
            meta.n_samples,
            meta.sample_rate_hz,
            meta.min_value,
            meta.max_value,
            meta.mean_value,
        ))

        segment_id = cur.lastrowid

        if store_samples:
            times = trace.times("utcdatetime")
            values = np.asarray(trace.data, dtype=np.float64)

            rows = [
                (segment_id, i, iso_time(times[i]), float(value))
                for i, value in enumerate(values)
                if math.isfinite(float(value))
            ]

            conn.executemany("""
                INSERT INTO sample
                    (segment_id, sample_index, sample_time, value)
                VALUES (?, ?, ?, ?)
            """, rows)

    conn.commit()
    return records

def ingest_directory(conn: sqlite3.Connection, data_dir: Path,
                      store_samples: bool = True):
    files = sorted(Path(data_dir).glob("*.mseed"))

    if not files:
        raise FileNotFoundError(
            f"No MiniSEED files found in {Path(data_dir).resolve()}"
        )

    all_records = []

    for path in files:
        print(f"Importing {path.name} ...")
        all_records.extend(
            ingest_file(conn, path, store_samples=store_samples)
        )

    return all_records

def write_metadata_json(records, output_path: Path):
    output_path.write_text(
        json.dumps([asdict(item) for item in records], indent=2),
        encoding="utf-8",
    )
