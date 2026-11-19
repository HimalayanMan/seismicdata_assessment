from seismicdata.db import initialize, connect

def test_schema_and_constraints(tmp_path):
    db = tmp_path / "test.sqlite"
    initialize(db)

    with connect(db) as conn:
        tables = {
            row[0]
            for row in conn.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """)
        }

        assert {
            "file",
            "network",
            "station",
            "channel",
            "waveform_segment",
            "sample",
        } <= tables

        conn.execute(
            "INSERT INTO network(code) VALUES (?)",
            ("XX",)
        )

        network_id = conn.execute(
            "SELECT network_id FROM network WHERE code='XX'"
        ).fetchone()[0]

        conn.execute("""
            INSERT INTO station(network_id, code, latitude, longitude)
            VALUES (?, ?, ?, ?)
        """, (network_id, "TEST", 38.0, -77.0))

        station_id = conn.execute(
            "SELECT station_id FROM station WHERE code='TEST'"
        ).fetchone()[0]

        conn.execute("""
            INSERT INTO channel(station_id, location_code, code, sample_rate_hz)
            VALUES (?, ?, ?, ?)
        """, (station_id, "00", "BHZ", 20.0))

        conn.commit()

        assert conn.execute(
            "SELECT COUNT(*) FROM channel"
        ).fetchone()[0] == 1
