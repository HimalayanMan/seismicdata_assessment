from __future__ import annotations

import requests
import pandas as pd

DEFAULT_URL = "https://service.earthscope.org/fdsnws/station/1"

def fetch_station_text(stations, base_url=DEFAULT_URL) -> pd.DataFrame:
    stations = sorted({
        str(station).strip()
        for station in stations
        if station and str(station).strip()
    })

    if not stations:
        return pd.DataFrame()

    url = base_url.rstrip("/") + "/query"

    response = requests.get(
        url,
        params={
            "station": ",".join(stations),
            "level": "station",
            "format": "text",
            "nodata": 404,
        },
        timeout=30,
    )
    response.raise_for_status()

    return parse_fdsn_station_text(response.text)

def parse_fdsn_station_text(text: str) -> pd.DataFrame:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    ]

    if not lines:
        return pd.DataFrame()

    header = [column.strip() for column in lines[0].split("|")]
    rows = [
        [value.strip() for value in line.split("|")]
        for line in lines[1:]
    ]

    df = pd.DataFrame(rows, columns=header)

    df = df.rename(columns={
        "Network": "network",
        "Station": "station",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Elevation": "elevation",
        "SiteName": "site_name",
    })

    for column in ["latitude", "longitude", "elevation"]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    return df

def merge_station_metadata(conn, station_df: pd.DataFrame):
    from .db import upsert_network, upsert_station

    if station_df.empty:
        return

    for row in station_df.to_dict("records"):
        network = str(row.get("network", "")).strip()
        station = str(row.get("station", "")).strip()

        if not network or not station:
            continue

        network_id = upsert_network(conn, network)

        upsert_station(
            conn,
            network_id,
            station,
            row.get("latitude"),
            row.get("longitude"),
            row.get("elevation"),
            row.get("site_name"),
        )

    conn.commit()
