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

    print("FDSN response:")
    print(response.text)

    return parse_fdsn_station_text(response.text)

def parse_fdsn_station_text(text: str) -> pd.DataFrame:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    ]

    if not lines:
        return pd.DataFrame()

    expected_columns = [
        "network",
        "station",
        "latitude",
        "longitude",
        "elevation",
        "site_name",
        "start_time",
        "end_time",
    ]

    # Split every non-comment line.
    rows = [
        [value.strip() for value in line.split("|")]
        for line in lines
    ]

    # Detect whether the first line is a header.
    first_row = [value.lower() for value in rows[0]]

    is_header = (
        "network" in first_row
        and "station" in first_row
        and "latitude" in first_row
        and "longitude" in first_row
    )

    if is_header:
        header = rows[0]
        data_rows = rows[1:]

        # Normalize known FDSN header names.
        header = [
            {
                "network": "network",
                "station": "station",
                "latitude": "latitude",
                "longitude": "longitude",
                "elevation": "elevation",
                "sitename": "site_name",
                "sitename": "site_name",
                "starttime": "start_time",
                "endtime": "end_time",
            }.get(column.lower(), column.lower())
            for column in header
        ]

        # If the service returned an unexpected header layout,
        # fall back to the known station schema.
        if len(header) != len(expected_columns):
            header = expected_columns

        columns = header

    else:
        # No header was returned. The first line is actual station data.
        data_rows = rows
        columns = expected_columns

    normalized_rows = []

    for row in data_rows:
        if len(row) < len(columns):
            row = row + [""] * (len(columns) - len(row))
        elif len(row) > len(columns):
            row = row[:len(columns)]

        normalized_rows.append(row)

    df = pd.DataFrame(
        normalized_rows,
        columns=columns,
    )

    # Ensure the columns required by the rest of the application
    # always have the expected names.
    rename_map = {
        "Network": "network",
        "Station": "station",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Elevation": "elevation",
        "SiteName": "site_name",
        "StartTime": "start_time",
        "EndTime": "end_time",
    }

    df = df.rename(columns=rename_map)

    for column in [
        "latitude",
        "longitude",
        "elevation",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
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
