from pathlib import Path
import html
import sqlite3

import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def metadata_summary(conn, output_csv: Path) -> pd.DataFrame:
    query = """
    SELECT f.filename,
           n.code AS network,
           s.code AS station,
           c.location_code,
           c.code AS channel,
           ws.start_time,
           ws.end_time,
           ws.n_samples,
           ws.sample_rate_hz,
           ws.data_min,
           ws.data_max,
           ws.data_mean,
           s.latitude,
           s.longitude,
           s.elevation_m
    FROM waveform_segment ws
    JOIN file f ON f.file_id = ws.file_id
    JOIN channel c ON c.channel_id = ws.channel_id
    JOIN station s ON s.station_id = c.station_id
    JOIN network n ON n.network_id = s.network_id
    ORDER BY f.filename, n.code, s.code, c.code
    """

    df = pd.read_sql_query(query, conn)
    df.to_csv(output_csv, index=False)
    return df

def _samples_for_file(conn, filename: str) -> pd.DataFrame:
    query = """
    SELECT sm.sample_time, sm.value
    FROM sample sm
    JOIN waveform_segment ws
      ON ws.segment_id = sm.segment_id
    JOIN file f
      ON f.file_id = ws.file_id
    WHERE f.filename = ?
    ORDER BY sm.sample_time
    """

    return pd.read_sql_query(
        query,
        conn,
        params=[filename],
        parse_dates=["sample_time"],
    )

def plot_helicorder(conn, filename: str, output_path: Path,
                    minutes_per_line: float = 1.0):
    df = _samples_for_file(conn, filename)

    if df.empty:
        return

    time_values = df["sample_time"].to_numpy()
    values = df["value"].to_numpy(dtype=float)

    start = time_values.min()
    elapsed_minutes = (
        (time_values - start) / np.timedelta64(1, "m")
    )

    line_number = np.floor(
        elapsed_minutes / minutes_per_line
    ).astype(int)

    fig, ax = plt.subplots(figsize=(15, 10))

    for line in np.unique(line_number):
        mask = line_number == line

        x = elapsed_minutes[mask] - (
            line * minutes_per_line
        )
        y = values[mask]

        median = np.nanmedian(y)
        scale = np.nanpercentile(
            np.abs(y - median), 95
        )

        if not np.isfinite(scale) or scale == 0:
            scale = 1.0

        y = (y - median) / scale

        ax.plot(
            x,
            line + 0.35 * y,
            linewidth=0.35,
        )

    ax.set_title(
        f"Helicorder-style waveform — {filename}"
    )
    ax.set_xlabel(
        f"Minutes within each {minutes_per_line:g}-minute line"
    )
    ax.set_ylabel("Elapsed line number")
    ax.grid(alpha=0.20)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

def build_station_map(conn, output_path: Path,
                      extra_stations: pd.DataFrame | None = None):
    stations = pd.read_sql_query("""
        SELECT n.code AS network,
               s.code AS station,
               s.latitude,
               s.longitude,
               s.elevation_m,
               s.site_name
        FROM station s
        JOIN network n
          ON n.network_id = s.network_id
        WHERE s.latitude IS NOT NULL
          AND s.longitude IS NOT NULL
        ORDER BY n.code, s.code
    """, conn)

    combined = stations.copy()

    if extra_stations is not None and not extra_stations.empty:
        extra = extra_stations.rename(
            columns={"elevation": "elevation_m"}
        ).copy()

        for column in ["site_name", "elevation_m"]:
            if column not in extra.columns:
                extra[column] = None

        extra = extra[
            [
                "network",
                "station",
                "latitude",
                "longitude",
                "elevation_m",
                "site_name",
            ]
        ]

        combined = pd.concat(
            [combined, extra],
            ignore_index=True,
        )

    combined = (
        combined
        .dropna(subset=["latitude", "longitude"])
        .drop_duplicates(["network", "station"])
    )

    if combined.empty:
        raise ValueError(
            "No station coordinates are available for the map."
        )

    center = [
        float(combined["latitude"].mean()),
        float(combined["longitude"].mean()),
    ]

    fmap = folium.Map(
        location=center,
        zoom_start=5,
        control_scale=True,
    )

    for row in combined.to_dict("records"):
        network = row["network"]
        station = row["station"]

        elevation = row.get("elevation_m")
        elevation_text = (
            f"{float(elevation):.1f} m"
            if pd.notna(elevation)
            else "N/A"
        )

        site = html.escape(
            str(row.get("site_name") or "N/A")
        )

        popup = (
            f"<b>{html.escape(network)}."
            f"{html.escape(station)}</b><br>"
            f"Site: {site}<br>"
            f"Latitude: {row['latitude']:.5f}<br>"
            f"Longitude: {row['longitude']:.5f}<br>"
            f"Elevation: {elevation_text}"
        )

        folium.Marker(
            location=[
                float(row["latitude"]),
                float(row["longitude"]),
            ],
            tooltip=f"{network}.{station}",
            popup=folium.Popup(
                popup,
                max_width=350,
            ),
        ).add_to(fmap)

    fmap.save(str(output_path))

def build_dashboard(summary: pd.DataFrame,
                    output_dir: Path,
                    dashboard_path: Path):
    rows = []

    for _, row in summary.iterrows():
        rows.append(
            f"""
            <tr>
              <td>{html.escape(str(row['filename']))}</td>
              <td>{html.escape(str(row['network']))}</td>
              <td>{html.escape(str(row['station']))}</td>
              <td>{html.escape(str(row['channel']))}</td>
              <td>{int(row['n_samples']):,}</td>
              <td>{float(row['sample_rate_hz']):.3f}</td>
              <td>{html.escape(str(row['start_time']))}</td>
              <td>{html.escape(str(row['end_time']))}</td>
            </tr>
            """
        )

    images = []

    for image in sorted(output_dir.glob("helicorder_*.png")):
        images.append(
            f"""
            <section>
              <h2>{html.escape(image.stem)}</h2>
              <img src="{html.escape(image.name)}"
                   style="max-width:100%; height:auto;">
            </section>
            """
        )

    table = "".join(rows)

    document = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SeismicData Assessment Dashboard</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 32px;
    line-height: 1.45;
}}
h1 {{ margin-bottom: 4px; }}
.metadata {{
    background: #f4f4f4;
    padding: 16px;
    border-radius: 6px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
}}
th, td {{
    border: 1px solid #bbb;
    padding: 6px;
    text-align: left;
}}
th {{ background: #eee; }}
iframe {{
    width: 100%;
    height: 650px;
    border: 1px solid #aaa;
}}
section {{ margin-top: 32px; }}
</style>
</head>

<body>
<h1>SeismicData Analysis Dashboard</h1>

<div class="metadata">
<h2>MiniSEED Metadata</h2>
<p>
This dashboard summarizes the MiniSEED records imported into the normalized
database and displays the generated helicorder-style waveform charts and
station map.
</p>
<p>
<b>Trace count:</b> {len(summary):,}<br>
<b>Source files:</b> {summary['filename'].nunique():,}<br>
<b>Stations:</b> {summary['station'].nunique():,}
</p>
</div>

<h2>Trace Metadata</h2>
<table>
<thead>
<tr>
<th>File</th>
<th>Network</th>
<th>Station</th>
<th>Channel</th>
<th>Samples</th>
<th>Rate Hz</th>
<th>Start</th>
<th>End</th>
</tr>
</thead>
<tbody>
{table}
</tbody>
</table>

<h2>Station Map</h2>
<iframe src="stations_map.html"></iframe>

{''.join(images)}

</body>
</html>
"""

    dashboard_path.write_text(
        document,
        encoding="utf-8",
    )
