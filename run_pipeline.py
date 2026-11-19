import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from seismicdata.config import DEFAULT_STATION_URL
from seismicdata.pipeline import run

def main():
    parser = argparse.ArgumentParser(
        description="Run the complete SeismicData assessment pipeline."
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/SEP"),
        help="Directory containing .mseed files.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for generated database/reports/charts.",
    )

    parser.add_argument(
        "--station-url",
        default=DEFAULT_STATION_URL,
        help="FDSN station service base URL.",
    )

    parser.add_argument(
        "--no-samples",
        action="store_true",
        help="Do not store individual waveform samples.",
    )

    args = parser.parse_args()

    run(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        station_url=args.station_url,
        store_samples=not args.no_samples,
    )

if __name__ == "__main__":
    main()
