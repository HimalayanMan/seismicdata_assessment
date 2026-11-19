# SeismicData — MiniSEED / FDSN / Database / Visualization Assessment

A complete, reproducible Python + Google Colab implementation for the
USGS SeismicData coding assessment.

## Assessment objectives implemented

- Read `SEP01.mseed`, `SEP02.mseed`, and `SEP03.mseed`
- Import MiniSEED data with ObsPy
- Create a normalized relational database
- Apply PK/FK/UNIQUE/CHECK constraints and indexes
- Import waveform metadata and samples
- Query IRIS/EarthScope FDSN station metadata
- Add station coordinates to the database
- Include required stations `HOA` and `SUG`
- Produce helicorder-style charts
- Produce an interactive station map with station icons
- Produce a metadata dashboard containing title + metadata + charts + map
- Provide SQL schema and reporting queries
- Provide a Colab notebook
- Provide tests and a demo-data generator
- Provide GitHub installation/push instructions

## Architecture

```text
                 ┌──────────────────────┐
                 │   Google Colab       │
                 │   main.ipynb         │
                 └──────────┬───────────┘
                            │
                            ▼
┌────────────────┐    ┌──────────────────┐
│ SEP*.mseed     │───▶│ ObsPy ingestion  │
└────────────────┘    └────────┬─────────┘
                               │
                               ▼
                       ┌───────────────┐
                       │ SQLite / SQL  │
                       │ normalized DB │
                       └───────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        Metadata report   Helico­rder       Station API
                           charts             │
                                              ▼
                                        HOA / SUG + local
                                        station coordinates
                                              │
                         ┌────────────────────┴───────────────┐
                         ▼                                    ▼
                  Static PNG charts                     HTML map
                         │                                    │
                         └────────────────┬───────────────────┘
                                          ▼
                                  HTML dashboard
```

## Repository structure

```text
seismicdata_assessment/
├── data/
│   └── SEP/
│       └── SEP01.mseed / SEP02.mseed / SEP03.mseed   # supplied by evaluator
├── docs/
│   ├── INSTALLATION.md
│   ├── DATABASE.md
│   └── ARCHITECTURE.md
├── notebooks/
│   └── main.ipynb
├── output/                                           # generated files
├── scripts/
│   └── create_demo_mseed.py
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── src/
│   └── seismicdata/
│       ├── __init__.py
│       ├── config.py
│       ├── db.py
│       ├── mseed.py
│       ├── station_api.py
│       ├── visualize.py
│       └── pipeline.py
├── tests/
│   ├── test_database.py
│   └── test_mseed.py
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── run_pipeline.py
└── README.md
```

## Quick start — Google Colab

```python
!git clone https://github.com/YOUR_GITHUB_USERNAME/seismicdata_assessment.git
%cd seismicdata_assessment
!pip install -r requirements.txt
```

Place the evaluator files in:

```text
data/SEP/SEP01.mseed
data/SEP/SEP02.mseed
data/SEP/SEP03.mseed
```

Run:

```python
!python run_pipeline.py --data-dir data/SEP --output-dir output
```

Or open:

```text
notebooks/main.ipynb
```

## Generated output

```text
output/
├── seismicdata.sqlite
├── metadata_summary.json
├── seismic_metadata.csv
├── station_api_results.csv
├── stations_of_interest.csv
├── database_summary.csv
├── helicorder_SEP01.png
├── helicorder_SEP02.png
├── helicorder_SEP03.png
├── stations_map.html
└── seismic_dashboard.html
```

The dashboard is the easiest artifact to review. It contains:

- project title
- data-file metadata
- waveform metadata
- helicorder charts
- station table
- interactive station map

## Database

The database is deliberately normalized:

```text
file
  │
  └── waveform_segment ── channel ── station ── network
              │
              └── sample
```

See `sql/schema.sql` and `docs/DATABASE.md`.

## API

The implementation uses the public FDSN Station Web Service. The default
endpoint is:

```text
https://service.earthscope.org/fdsnws/station/1
```

The original assessment references the IRIS endpoint:

```text
https://service.iris.edu/fdsnws/station/1/
```

The project uses the current EarthScope service endpoint while preserving
the FDSN interface expected by the assessment.

## Production-quality considerations

For assessment-sized data, individual waveform samples are stored in SQLite
so the evaluator can inspect relational data directly.

For very large production datasets, the recommended design is to retain
MiniSEED as the authoritative waveform object and store metadata plus
derived/downsampled waveform data in the database. The ingestion command
therefore supports:

```bash
python run_pipeline.py --no-samples
```

## Testing

```bash
pytest -q
```

## Demo data

If the evaluator files are not available, generate small synthetic MiniSEED
files only for local development:

```bash
python scripts/create_demo_mseed.py
python run_pipeline.py --data-dir data/DEMO --output-dir output
```

The demo data is not part of the assessment submission.

## GitHub

See `docs/INSTALLATION.md` for exact commands to create the repository,
push it from Colab, and verify it from a clean clone.
