from pathlib import Path

DEFAULT_STATION_URL = "https://service.earthscope.org/fdsnws/station/1"
DEFAULT_DB_NAME = "seismicdata.sqlite"

def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
