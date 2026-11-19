from pathlib import Path
import sys

import numpy as np
from obspy import Stream, Trace, UTCDateTime

from seismicdata.db import initialize, connect
from seismicdata.mseed import ingest_file

def create_trace(path: Path):
    data = np.arange(100, dtype=np.float32)

    trace = Trace(data=data)
    trace.stats.network = "XX"
    trace.stats.station = "TEST"
    trace.stats.location = "00"
    trace.stats.channel = "BHZ"
    trace.stats.starttime = UTCDateTime("2026-01-01T00:00:00Z")
    trace.stats.sampling_rate = 10.0

    Stream([trace]).write(
        str(path),
        format="MSEED",
    )

def test_mseed_import(tmp_path):
    mseed = tmp_path / "TEST.mseed"
    db = tmp_path / "test.sqlite"

    create_trace(mseed)
    initialize(db)

    with connect(db) as conn:
        records = ingest_file(conn, mseed, store_samples=True)

        assert len(records) == 1
        assert records[0].station == "TEST"

        assert conn.execute(
            "SELECT COUNT(*) FROM file"
        ).fetchone()[0] == 1

        assert conn.execute(
            "SELECT COUNT(*) FROM sample"
        ).fetchone()[0] == 100
