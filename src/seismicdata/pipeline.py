from pathlib import Path
import pandas as pd

from .config import DEFAULT_STATION_URL, ensure_dir
from .db import connect, initialize
from .mseed import ingest_directory, write_metadata_json
from .station_api import fetch_station_text, merge_station_metadata
from .visualize import (
    build_dashboard,
    build_station_map,
    metadata_summary,
    plot_helicorder,
)

def run(data_dir: Path, output_dir: Path,
        station_url: str = DEFAULT_STATION_URL,
        store_samples: bool = True):

    output_dir = ensure_dir(output_dir)
    db_path = output_dir / "seismicdata.sqlite"

    initialize(db_path)

    with connect(db_path) as conn:
        records = ingest_directory(
            conn,
            data_dir,
            store_samples=store_samples,
        )

        write_metadata_json(
            records,
            output_dir / "metadata_summary.json",
        )

        station_codes = sorted({
            record.station
            for record in records
            if record.station
        })

        station_df = pd.DataFrame()

        if station_codes:
            try:
                print("Querying station metadata API ...")

                station_df = fetch_station_text(
                    station_codes,
                    station_url,
                )

                merge_station_metadata(
                    conn,
                    station_df,
                )

                station_df.to_csv(
                    output_dir / "station_api_results.csv",
                    index=False,
                )

            except Exception as exc:
                print(
                    f"WARNING: station API request failed: {exc}"
                )

        summary = metadata_summary(
            conn,
            output_dir / "seismic_metadata.csv",
        )

        for filename in sorted(
            summary["filename"].unique()
        ):
            print(
                f"Creating helicorder for {filename} ..."
            )

            plot_helicorder(
                conn,
                filename,
                output_dir /
                f"helicorder_{Path(filename).stem}.png",
            )

        interest_df = pd.DataFrame()

        try:
            print("Querying required stations HOA and SUG ...")

            interest_df = fetch_station_text(
                ["HOA", "SUG"],
                station_url,
            )

            if not interest_df.empty:
                interest_df.to_csv(
                    output_dir /
                    "stations_of_interest.csv",
                    index=False,
                )

                merge_station_metadata(
                    conn,
                    interest_df,
                )

        except Exception as exc:
            print(
                f"WARNING: HOA/SUG station request failed: {exc}"
            )

        build_station_map(
            conn,
            output_dir / "stations_map.html",
            extra_stations=interest_df,
        )

        # Re-read after station enrichment so the dashboard uses
        # the final database state.
        summary = metadata_summary(
            conn,
            output_dir / "seismic_metadata.csv",
        )

        build_dashboard(
            summary,
            output_dir,
            output_dir / "seismic_dashboard.html",
        )

        # Simple database summary.
        db_summary = pd.DataFrame([
            ["files", conn.execute("SELECT COUNT(*) FROM file").fetchone()[0]],
            ["networks", conn.execute("SELECT COUNT(*) FROM network").fetchone()[0]],
            ["stations", conn.execute("SELECT COUNT(*) FROM station").fetchone()[0]],
            ["channels", conn.execute("SELECT COUNT(*) FROM channel").fetchone()[0]],
            ["segments", conn.execute("SELECT COUNT(*) FROM waveform_segment").fetchone()[0]],
            ["samples", conn.execute("SELECT COUNT(*) FROM sample").fetchone()[0]],
        ], columns=["object", "count"])

        db_summary.to_csv(
            output_dir / "database_summary.csv",
            index=False,
        )

    print("\nPipeline complete.")
    print(f"Database: {db_path.resolve()}")
    print(f"Dashboard: {(output_dir / 'seismic_dashboard.html').resolve()}")

    return db_path
