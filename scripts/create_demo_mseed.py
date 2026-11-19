from pathlib import Path
import sys
import numpy as np
from obspy import Stream, Trace, UTCDateTime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

out = ROOT / "data" / "DEMO"
out.mkdir(parents=True, exist_ok=True)

start = UTCDateTime("2026-01-01T00:00:00Z")
sample_rate = 20.0
duration_seconds = 300

rng = np.random.default_rng(42)

for index, station in enumerate(["DEMO1", "DEMO2", "DEMO3"], start=1):
    t = np.arange(0, duration_seconds, 1 / sample_rate)

    signal = (
        0.10 * np.sin(2 * np.pi * 1.0 * t)
        + 0.05 * np.sin(2 * np.pi * 3.0 * t)
        + 0.01 * rng.normal(size=len(t))
    )

    trace = Trace(data=signal.astype(np.float32))
    trace.stats.network = "XX"
    trace.stats.station = station
    trace.stats.location = "00"
    trace.stats.channel = "BHZ"
    trace.stats.starttime = start
    trace.stats.sampling_rate = sample_rate

    Stream([trace]).write(
        str(out / f"DEMO{index}.mseed"),
        format="MSEED",
    )

print(f"Created demo MiniSEED files in {out}")
